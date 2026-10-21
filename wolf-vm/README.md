# 🐺 WOLF-VM — The Workshop | Módulo 03

**Build. Break. Understand. Rebuild.**

**Something Crazy | 22–31 outubro 2026 | v0.1**

CPU virtual didática em C11, com assembler Python 3.9+, bytecode WVM1 e 17 testes positivos e negativos. Não é hipervisor, não roda x86 e não executa sistemas operacionais convidados.

## Requisitos

- C11 compiler: cc ou gcc
- make
- Python 3.9+

## Executar

    cd wolf-vm
    make
    make examples
    ./build/wolfvm --trace build/examples/arith.wvm
    make test

A saída do primeiro exemplo termina com R0=8.

## Montar programas

    python3 tools/assemble.py examples/loop.wva -o build/examples/loop.wvm
    ./build/wolfvm --trace build/examples/loop.wvm

## Estrutura

- src/: interpretador, loader e CLI.
- include/: estado e ISA da VM.
- tools/: assembler WVA → WVM.
- examples/: aritmética, loop, memória, CALL/RET.
- tests/: 17 casos de execução e bytecode inválido.
- docs/architecture.md: contrato de arquitetura.
- docs/security.md: check-up, controles e riscos residuais.

## Garantias e limites

O bytecode não tem instruções para abrir sockets, acessar arquivos do host ou executar processos externos. A VM valida registradores, tamanho do arquivo, offsets de instruções, acessos de memória e profundidade de pilha. Execução limitada a 100.000 passos por padrão. A v0.1 é experimental e não é uma sandbox auditada para código hostil.

O site Workshop Labs publica documentação, não um interpretador remoto.

Documentação pública planejada: https://workshop-labs.pages.dev/projects/wolf-vm/ (depende de deploy Cloudflare independente).
