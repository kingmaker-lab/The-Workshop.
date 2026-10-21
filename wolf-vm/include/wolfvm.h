#ifndef WOLFVM_H
#define WOLFVM_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define WVM_MAX_CODE (64u * 1024u)
#define WVM_MEM_SIZE (64u * 1024u)
#define WVM_STACK_CAP 256u
#define WVM_REG_COUNT 8u

/* WVM1: magic[4], version[1], flags[1], reserved[2], code_size_le[4]. */
#define WVM_HEADER_SIZE 12u

enum {
    WVM_NOP = 0x00,
    WVM_HALT = 0x01,
    WVM_MOVI = 0x10,
    WVM_MOV = 0x11,
    WVM_ADD = 0x20,
    WVM_SUB = 0x21,
    WVM_XOR = 0x22,
    WVM_CMP = 0x30,
    WVM_JMP = 0x40,
    WVM_JZ = 0x41,
    WVM_JNZ = 0x42,
    WVM_PUSH = 0x50,
    WVM_POP = 0x51,
    WVM_CALL = 0x52,
    WVM_RET = 0x53,
    WVM_LOAD = 0x60,
    WVM_STORE = 0x61,
};

typedef struct {
    uint8_t code[WVM_MAX_CODE];
    uint8_t memory[WVM_MEM_SIZE];
    uint8_t boundary[WVM_MAX_CODE];
    uint32_t regs[WVM_REG_COUNT];
    uint32_t stack[WVM_STACK_CAP];
    uint32_t code_size;
    uint32_t pc;
    uint32_t sp; /* Number of entries in stack; 0 means empty. */
    uint32_t steps;
    bool zf;
    char error[256];
} WolfVM;

bool wvm_load(WolfVM *vm, const char *path);
bool wvm_validate(WolfVM *vm);
bool wvm_run(WolfVM *vm, uint32_t max_steps, bool trace);

#endif
