# Security Check-up 001 — WOLF-VM v0.1

## Controles

- Bytecode interpretado em C, não executado como instrução nativa.
- Arquivo lido apenas pelo loader CLI; nenhuma instrução abre arquivos ou sockets.
- Validação completa de cabeçalho e tamanho; rejeição de bytecode truncado.
- Rejeição de opcode desconhecido, registrador inválido e saltos não alinhados ao início de instrução.
- LOAD/STORE de 32 bits somente dentro da RAM virtual, com alinhamento.
- Rejeição de stack overflow, underflow e retorno inválido.
- Limite de passos configurável (100 mil padrão, 1 milhão máximo).
- Trace limitado a 1000 eventos; aritmética unsigned com overflow definido.

## Limitações

- NÃO é sandbox auditada para entradas arbitrárias hostis.
- CPU, memória e tempo precisam de limites externos antes de execução remota.
- PUSH e CALL compartilham pilha; manipulação dos endereços pode causar traps controladas.
- Sem fuzzing sistemático, auditoria independente, provas formais ou mitigação de side channels.

## Deploy seguro

Cloudflare Pages hospeda apenas páginas estáticas e links para código. Não execute bytecode enviado por visitantes no Worker. Uma API futura exigiria isolamento robusto, autorização/quotas, limites de recursos, monitoramento e auditoria.
