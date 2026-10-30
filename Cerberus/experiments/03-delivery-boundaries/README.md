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

A partir de `Cerberus`:

```sh
node --test experiments/03-delivery-boundaries/model.test.mjs
```

Os testes injetam falha antes da entrega e falha após o processamento, mas antes do *ack*. Na segunda situação há duas tentativas de entrega e somente um efeito no consumidor idempotente.

## Hipótese e observação

**Hipótese:** introduzir uma fronteira assíncrona cria o problema de entrega duplicada após a perda do reconhecimento, mesmo quando o consumidor concluiu o trabalho. Idempotência no consumidor reduz o efeito duplicado.

**Observação reproduzível:** os testes verificam os estados e os efeitos dessa máquina local. **Não** medem latência p95, throughput, confiabilidade real de filas, segurança ou custo de operação.


## Parte 2 — outbox persistente + HTTP local com SQLite

A continuação em [sqlite_http/](sqlite_http/) adiciona **duas bases SQLite independentes**:
uma para reservas/outbox e outra para o consumidor. Reservas e eventos pendentes
são persistidos em **uma mesma transação**. A entrega ocorre por HTTP limitado
a `127.0.0.1`, e o consumidor grava o efeito com chave única por evento.

Executar a partir da raiz do repositório (Python 3.11+; somente biblioteca padrão):

```sh
python -m unittest discover -s Cerberus/experiments/03-delivery-boundaries/sqlite_http -p 'test_*.py' -v
```

Os testes exercitam rollback transacional, reinicialização dos repositórios,
entrega por HTTP de loopback, erro 409, rejeição de payload e deduplicação após
falha de confirmação. Não há servidor público, agendador de retry, filas reais,
comunicação autenticada, concorrência distribuída nem benchmark p95.

**Sequência central, reproduzível:** o produtor faz commit da reserva e outbox
→ o consumidor recebe e faz commit da notificação via HTTP → o produtor simula
uma falha antes de gravar o ack → dois bancos são reabertos → há uma segunda
entrega, mas somente **uma** notificação persistida. Isso demonstra idempotência
nesse cenário controlado, não garantia geral de exactly-once.

## Próximos incrementos

1. **Concluído em laboratório:** SQLite transacional e persistência de outbox, reinícios e HTTP loopback com testes de falhas.
2. **Próximo:** backoff, limite de tentativas, dead-letter e concorrência entre despachantes.
3. **Próximo:** benchmarks isolados e documentados, com limites explícitos.
4. **Próximo:** avaliar duas instâncias/processos isolados e um ADR revisado com evidências.

**Segurança:** exercício sem dados pessoais, autenticação ou autorização; não exponha esta simulação como serviço público. É código pedagógico, não produção.

Decisão inicial: [ADR-0003](ADR-0003-delivery-boundary.md).
