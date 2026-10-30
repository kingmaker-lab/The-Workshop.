# CERBERUS 03 — Fronteiras de entrega e falhas

> **Parte 1 do ciclo 03:** observar como uma fronteira de mensagens modifica os modos de falha, sem alegar ganhos automáticos com microsserviços.

## Pergunta

Se um serviço de reservas precisar notificar outro componente, o que muda ao sair de uma chamada local síncrona para uma entrega de evento com confirmação e possibilidade de repetição?

Dois modelos mínimos, com as mesmas validações:

| Modelo | Comportamento | Limitação |
|---|---|---|
| Chamada local | Cria a reserva e a notificação no mesmo fluxo síncrono. | Não representa uma transação real nem isolamento entre processos. |
| Entrega de evento | Cria reserva + entrada de outbox em memória; um despachante entrega e confirma. | Simulação em um só processo; sem broker, durabilidade ou rede real. |

## Executar (Node.js >= 20)

A partir de \`Cerberus\`:

\`\`\`sh
node --test experiments/03-delivery-boundaries/model.test.mjs
\`\`\`

Os testes injetam falha antes da entrega e falha após o processamento, mas antes do *ack*. Na segunda situação há duas tentativas de entrega e somente um efeito no consumidor idempotente.

## Hipótese e observação

**Hipótese:** introduzir uma fronteira assíncrona cria o problema de entrega duplicada após a perda do reconhecimento, mesmo quando o consumidor concluiu o trabalho. Idempotência no consumidor reduz o efeito duplicado.

**Observação reproduzível:** os testes verificam os estados e os efeitos dessa máquina local. **Não** medem latência p95, throughput, confiabilidade real de filas, segurança ou custo de operação.

## Próximos incrementos

1. Persistência transacional em SQLite para reservas e outbox, com testes de reinício.
2. Comunicação real por HTTP local, com timeouts e injeção de falhas.
3. Benchmarks isolados e documentados, comparando custos de serialização e infraestrutura sem generalizações.
4. ADR com evidências para decidir quando separar deploys.

**Segurança:** exercício sem dados pessoais, autenticação ou autorização; não exponha esta simulação como serviço público. É código pedagógico, não produção.

Decisão inicial: [ADR-0003](ADR-0003-delivery-boundary.md).
