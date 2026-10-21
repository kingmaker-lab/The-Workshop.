#include "wolfvm.h"

#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void usage(const char *exe) {
    fprintf(stderr, "uso: %s [--trace] [--max-steps N] programa.wvm\n", exe);
}

int main(int argc, char **argv) {
    WolfVM *vm;
    const char *path = NULL;
    uint32_t max_steps = 100000;
    bool trace = false;
    int status = EXIT_FAILURE;
    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--trace")) trace = true;
        else if (!strcmp(argv[i], "--max-steps") && i + 1 < argc) {
            char *end = NULL;
            unsigned long n = strtoul(argv[++i], &end, 10);
            if (!argv[i][0] || !end || *end || n < 1 || n > 1000000) {
                fprintf(stderr, "--max-steps: use um numero entre 1 e 1000000\n");
                return EXIT_FAILURE;
            }
            max_steps = (uint32_t)n;
        } else if (!path && argv[i][0] != '-') path = argv[i];
        else { usage(argv[0]); return EXIT_FAILURE; }
    }
    if (!path) { usage(argv[0]); return EXIT_FAILURE; }
    vm = calloc(1, sizeof *vm);
    if (!vm) { fprintf(stderr, "falha de memoria\n"); return EXIT_FAILURE; }
    if (!wvm_load(vm, path) || !wvm_run(vm, max_steps, trace)) {
        fprintf(stderr, "[WOLF-VM ERRO] %s\n", vm->error);
        goto done;
    }
    printf("HALT steps=%" PRIu32 " PC=%" PRIu32 " SP=%" PRIu32 " ZF=%u\n",
           vm->steps, vm->pc, vm->sp, (unsigned)vm->zf);
    for (unsigned i = 0; i < WVM_REG_COUNT; ++i)
        printf("R%u=%" PRIu32 "%c", i, vm->regs[i], i == WVM_REG_COUNT - 1 ? '\n' : ' ');
    status = EXIT_SUCCESS;
done:
    free(vm);
    return status;
}
