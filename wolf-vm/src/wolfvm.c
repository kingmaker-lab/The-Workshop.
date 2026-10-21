#include "wolfvm.h"

#include <inttypes.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>

static bool fail(WolfVM *vm, const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(vm->error, sizeof vm->error, fmt, ap);
    va_end(ap);
    return false;
}

static uint16_t rd16(const uint8_t *p) {
    return (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8));
}

static uint32_t rd32(const uint8_t *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

static void wr32(uint8_t *p, uint32_t n) {
    p[0] = (uint8_t)n;
    p[1] = (uint8_t)(n >> 8);
    p[2] = (uint8_t)(n >> 16);
    p[3] = (uint8_t)(n >> 24);
}

static uint32_t instr_size(uint8_t op) {
    switch (op) {
        case WVM_NOP: case WVM_HALT: case WVM_RET: return 1;
        case WVM_PUSH: case WVM_POP: return 2;
        case WVM_MOV: case WVM_ADD: case WVM_SUB:
        case WVM_XOR: case WVM_CMP: return 3;
        case WVM_LOAD: case WVM_STORE: return 4;
        case WVM_JMP: case WVM_JZ: case WVM_JNZ: case WVM_CALL: return 5;
        case WVM_MOVI: return 6;
        default: return 0;
    }
}

bool wvm_load(WolfVM *vm, const char *path) {
    FILE *f;
    uint8_t hdr[WVM_HEADER_SIZE];
    uint32_t declared;
    long n;
    memset(vm, 0, sizeof *vm);
    f = fopen(path, "rb");
    if (!f) return fail(vm, "nao foi possivel abrir o arquivo: %s", path);
    if (fseek(f, 0, SEEK_END) != 0 || (n = ftell(f)) < 0 ||
        fseek(f, 0, SEEK_SET) != 0) {
        fclose(f);
        return fail(vm, "nao foi possivel medir o arquivo");
    }
    if (n < (long)WVM_HEADER_SIZE || n > (long)(WVM_HEADER_SIZE + WVM_MAX_CODE)) {
        fclose(f);
        return fail(vm, "tamanho de arquivo invalido");
    }
    if (fread(hdr, 1, sizeof hdr, f) != sizeof hdr) {
        fclose(f);
        return fail(vm, "cabecalho incompleto");
    }
    if (memcmp(hdr, "WVM1", 4) || hdr[4] != 1 || hdr[5] != 0 || rd16(hdr + 6) != 0) {
        fclose(f);
        return fail(vm, "formato/versao/flags invalidos");
    }
    declared = rd32(hdr + 8);
    if (declared == 0 || declared > WVM_MAX_CODE || n != (long)(WVM_HEADER_SIZE + declared)) {
        fclose(f);
        return fail(vm, "comprimento do bytecode invalido");
    }
    if (fread(vm->code, 1, declared, f) != declared) {
        fclose(f);
        return fail(vm, "bytecode truncado");
    }
    fclose(f);
    vm->code_size = declared;
    return wvm_validate(vm);
}

bool wvm_validate(WolfVM *vm) {
    uint32_t pc = 0;
    memset(vm->boundary, 0, sizeof vm->boundary);
    if (vm->code_size == 0 || vm->code_size > WVM_MAX_CODE)
        return fail(vm, "tamanho de codigo invalido");

    while (pc < vm->code_size) {
        uint8_t op = vm->code[pc];
        uint32_t len = instr_size(op);
        if (len == 0) return fail(vm, "opcode desconhecido 0x%02x em PC=%" PRIu32, op, pc);
        if (len > vm->code_size - pc)
            return fail(vm, "instrucao truncada em PC=%" PRIu32, pc);
        vm->boundary[pc] = 1;
        switch (op) {
            case WVM_MOVI: case WVM_PUSH: case WVM_POP: case WVM_LOAD:
                if (vm->code[pc + 1] >= WVM_REG_COUNT)
                    return fail(vm, "registrador invalido em PC=%" PRIu32, pc);
                break;
            case WVM_MOV: case WVM_ADD: case WVM_SUB:
            case WVM_XOR: case WVM_CMP:
                if (vm->code[pc + 1] >= WVM_REG_COUNT ||
                    vm->code[pc + 2] >= WVM_REG_COUNT)
                    return fail(vm, "registrador invalido em PC=%" PRIu32, pc);
                break;
            case WVM_STORE:
                if (vm->code[pc + 3] >= WVM_REG_COUNT)
                    return fail(vm, "registrador invalido em PC=%" PRIu32, pc);
                break;
            default: break;
        }
        if (op == WVM_LOAD || op == WVM_STORE) {
            uint16_t addr = rd16(vm->code + pc + (op == WVM_LOAD ? 2 : 1));
            if (addr % 4 != 0 || (uint32_t)addr > WVM_MEM_SIZE - 4)
                return fail(vm, "acesso de memoria desalinhado ou fora dos limites em PC=%" PRIu32, pc);
        }
        pc += len;
    }
    /* Only jumps to instruction boundaries are accepted, not bytes within immediates. */
    for (pc = 0; pc < vm->code_size; pc += instr_size(vm->code[pc])) {
        uint8_t op = vm->code[pc];
        if (op == WVM_JMP || op == WVM_JZ || op == WVM_JNZ || op == WVM_CALL) {
            uint32_t target = rd32(vm->code + pc + 1);
            if (target >= vm->code_size || !vm->boundary[target])
                return fail(vm, "salto invalido de PC=%" PRIu32 " para PC=%" PRIu32, pc, target);
        }
    }
    return true;
}

static bool push(WolfVM *vm, uint32_t n) {
    if (vm->sp == WVM_STACK_CAP) return fail(vm, "stack overflow em PC=%" PRIu32, vm->pc);
    vm->stack[vm->sp++] = n;
    return true;
}

static bool pop(WolfVM *vm, uint32_t *n) {
    if (vm->sp == 0) return fail(vm, "stack underflow em PC=%" PRIu32, vm->pc);
    *n = vm->stack[--vm->sp];
    return true;
}

bool wvm_run(WolfVM *vm, uint32_t max_steps, bool trace) {
    if (max_steps == 0) return fail(vm, "max_steps deve ser positivo");
    while (vm->steps < max_steps) {
        uint32_t pc = vm->pc, next, a, b;
        uint8_t op;
        if (pc >= vm->code_size || !vm->boundary[pc])
            return fail(vm, "PC invalido: %" PRIu32 " (programa sem HALT?)", pc);
        op = vm->code[pc];
        next = pc + instr_size(op);
        if (trace && vm->steps < 1000)
            printf("[TRACE] step=%" PRIu32 " PC=%" PRIu32 " OP=0x%02x SP=%" PRIu32 " ZF=%u R0=%" PRIu32 "\n",
                   vm->steps, pc, op, vm->sp, (unsigned)vm->zf, vm->regs[0]);
        else if (trace && vm->steps == 1000)
            puts("[TRACE] exibicao limitada a 1000 instrucoes");
        vm->pc = next;
        vm->steps++;
        switch (op) {
            case WVM_NOP: break;
            case WVM_HALT: return true;
            case WVM_MOVI:
                vm->regs[vm->code[pc + 1]] = rd32(vm->code + pc + 2);
                break;
            case WVM_MOV:
                vm->regs[vm->code[pc + 1]] = vm->regs[vm->code[pc + 2]];
                break;
            case WVM_ADD:
                a = vm->code[pc + 1]; b = vm->code[pc + 2];
                vm->regs[a] += vm->regs[b]; break;
            case WVM_SUB:
                a = vm->code[pc + 1]; b = vm->code[pc + 2];
                vm->regs[a] -= vm->regs[b]; break;
            case WVM_XOR:
                a = vm->code[pc + 1]; b = vm->code[pc + 2];
                vm->regs[a] ^= vm->regs[b]; break;
            case WVM_CMP:
                vm->zf = vm->regs[vm->code[pc + 1]] == vm->regs[vm->code[pc + 2]];
                break;
            case WVM_JMP:
                vm->pc = rd32(vm->code + pc + 1); break;
            case WVM_JZ:
                if (vm->zf) vm->pc = rd32(vm->code + pc + 1);
                break;
            case WVM_JNZ:
                if (!vm->zf) vm->pc = rd32(vm->code + pc + 1);
                break;
            case WVM_PUSH:
                if (!push(vm, vm->regs[vm->code[pc + 1]])) return false;
                break;
            case WVM_POP:
                if (!pop(vm, &vm->regs[vm->code[pc + 1]])) return false;
                break;
            case WVM_CALL:
                if (!push(vm, next)) return false;
                vm->pc = rd32(vm->code + pc + 1);
                break;
            case WVM_RET:
                if (!pop(vm, &vm->pc)) return false;
                if (vm->pc >= vm->code_size || !vm->boundary[vm->pc])
                    return fail(vm, "RET tentou acessar PC invalido: %" PRIu32, vm->pc);
                break;
            case WVM_LOAD:
                a = rd16(vm->code + pc + 2);
                vm->regs[vm->code[pc + 1]] = rd32(vm->memory + a);
                break;
            case WVM_STORE:
                a = rd16(vm->code + pc + 1);
                wr32(vm->memory + a, vm->regs[vm->code[pc + 3]]);
                break;
            default:
                return fail(vm, "erro interno: instrucao nao reconhecida");
        }
    }
    return fail(vm, "limite de execucao atingido (%" PRIu32 " instrucoes)", max_steps);
}
