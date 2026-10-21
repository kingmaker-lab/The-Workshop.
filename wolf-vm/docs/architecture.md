# WOLF-VM — Contrato de arquitetura v0.1

Interpretador didático determinístico sem syscalls de host. Não é hipervisor, nem executa instruções x86 nativas.

## Máquina

- 8 registradores R0..R7, 32 bits sem sinal;
- PC: offset do bytecode, inicialmente zero;
- SP: número de entradas ocupadas em pilha de 256 palavras uint32;
- ZF: atualizado por CMP (flag de igualdade);
- Código: máximo 65536 bytes, separado da RAM de dados (65536 bytes);
- LOAD/STORE: little-endian, somente acessos alinhados a 4 bytes;
- Aritmética sem sinal com transbordamento módulo 2^32;
- Bytecode sem acesso direto a recursos do sistema hospedeiro.

## Cabeçalho WVM1 (12 bytes)

Offset 0: ASCII "WVM1" (4 bytes). Offset 4: version=1 (1 byte).
Offset 5: flags=0 (1 byte). Offset 6: reservado=0 (2 bytes).
Offset 8: code_size (uint32 little-endian). Offset 12: início do bytecode.

A VM rejeita código truncado, excessivo, inválido e saltos para bytes internos de instruções.

## ISA v0.1

| Hex | Instrucao | Operandos | Bytes |
|---|---|---|---|
| 00 | NOP | - | 1 |
| 01 | HALT | - | 1 |
| 10 | MOVI | registro, imediato32 | 6 |
| 11 | MOV | registro, registro | 3 |
| 20 | ADD | registro, registro | 3 |
| 21 | SUB | registro, registro | 3 |
| 22 | XOR | registro, registro | 3 |
| 30 | CMP | registro, registro | 3 |
| 40 | JMP | endereço32 | 5 |
| 41 | JZ | endereço32 | 5 |
| 42 | JNZ | endereço32 | 5 |
| 50 | PUSH | registro | 2 |
| 51 | POP | registro | 2 |
| 52 | CALL | endereço32 | 5 |
| 53 | RET | - | 1 |
| 60 | LOAD | registro, endereço16 | 4 |
| 61 | STORE | endereço16, registro | 4 |

Todo inteiro multibyte é little-endian; PC avança com instruções sequenciais ou recebe destino de salto.

Próximos estudos: I/O com capacidades explícitas, debugger, snapshots e fuzzing.
