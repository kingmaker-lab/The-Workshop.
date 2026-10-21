# 🐺 WOLF-VM — Módulo 03 (v0.1)

**The Workshop • 22–31 de outubro de 2026 • Something Crazy**

Máquina virtual educacional em C11, com assembler em Python e bytecode WVM1. Inclui 8 registradores de 32 bits, PC/SP/ZF, pilha, memória, instruções aritméticas, saltos e chamadas, validação prévia de bytecode e proteção por limite de instruções.

## Distribuição

O pacote de código-fonte completo está em `wolf-vm-v0.1-source.tar.gz` neste diretório (sem binários compilados). Para usar:

```sh
mkdir -p wolf-vm-workdir
cd wolf-vm-workdir
tar -xzf ../wolf-vm-v0.1-source.tar.gz
make
make examples
make test
./build/wolfvm --trace build/examples/arith.wvm
```

Resultados locais: **17 testes aprovados**. Interface em Cloudflare Pages: [WOLF-VM](https://workshop-labs.pages.dev/projects/wolf-vm/) (deploy de Pages realizado separadamente).

## Aviso

A v0.1 **não é sandbox auditada para código hostil** e não executa instruções enviadas por visitantes no Cloudflare. I/O, debugger avançado e fuzzing ficam para experimentos posteriores. Consulte `docs/security.md` no pacote de código.
