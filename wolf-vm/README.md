# 🐺 WOLF-VM — Módulo 03 (v0.1)

**The Workshop • 22–31 de outubro de 2026 • Something Crazy**

Máquina virtual educacional em C11, com assembler em Python e bytecode WVM1. Projeto experimental com 8 registradores de 32 bits, PC/SP/ZF, pilha, memória, instruções aritméticas, saltos, chamadas e validação de bytecode.

## Status de integração

- A página técnica e o card do WOLF-VM estão **versionados em branch**, pendentes de revisão, merge e publicação separada do Cloudflare Pages.
- O código-fonte v0.1 foi compilado e executou **17 testes locais com sucesso**.
- **O pacote completo do interpretador ainda não foi enviado a este repositório.** Está disponível como anexo `wolf-vm-v0.1.zip` na conversa de desenvolvimento. É necessário adicionar seus arquivos em `wolf-vm/` antes de considerar a integração de código concluída.
- I/O, debugger avançado e fuzzing continuam no roadmap.

## Rodar após importar o código

```sh
cd wolf-vm
make
make examples
make test
./build/wolfvm --trace build/examples/arith.wvm
```

## Segurança

O Cloudflare hospeda exclusivamente documentação estática, sem executar bytecode enviado por visitantes. O interpretador v0.1 **não é uma sandbox auditada para cargas hostis**.
