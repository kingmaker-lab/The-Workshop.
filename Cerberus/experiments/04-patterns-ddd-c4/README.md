# CERBERUS 04 | Design Patterns, DDD, C4 e ADR

Quarta bancada educacional do The Workshop Software Architecture Lab.

## Pergunta

Como preservar as regras de uma reserva sem acoplar o núcleo a um mecanismo de armazenamento, uma política fixa de capacidade ou ao formato interno de notificações?

**Hipótese:** separar a aggregate root Schedule, a política de capacidade injetável, a aplicação e o adaptador entre bounded contexts pode reduzir razões de mudança para o cenário pequeno.

Não é uma promessa de melhor desempenho, escalabilidade ou manutenibilidade em todo software.

## Rodar os testes

Usar Node.js 20 ou superior, sem dependências externas. A partir da raiz de Cerberus:

    node --test experiments/04-patterns-ddd-c4/lab04.test.mjs
    npm test

Nenhum servidor é iniciado e nenhum dado pessoal é armazenado.

## Mapa de decisões

| Ideia | Componente | Critério demonstrado |
|---|---|---|
| SRP | Schedule, ReserveSeats, toNotificationDraft | Domínio, orquestração e tradução têm papéis separados |
| OCP / Strategy | standardPolicy e smallGroupPolicy | Troca de política sem editar o caso de uso |
| DIP / Ports & Adapters | ReserveSeats depende da porta load/commit | Sem import de SQLite, framework ou transporte |
| DDD / aggregate | Schedule.reserve | Capacidade, idempotência e evento de domínio |
| Bounded contexts | Reservations e Communications | Tradução de um contrato de integração explícito |
| C4 | C4.md | Contexto e containers lógicos, com limites declarados |
| ADR | ADR-0004.md | Escolha, alternativas, consequências e reavaliação |

## Artefatos

- Código do domínio e estratégias: domain.mjs.
- Aplicação e repositório em memória: application.mjs.
- Tradução para Comunicações: communications.mjs.
- Testes reproduzíveis: lab04.test.mjs.
- Diagramas: [C4.md](C4.md).
- Registro arquitetural: [ADR-0004.md](ADR-0004.md).

## Limites

O exemplo é sequencial e só usa memória. Não oferece persistência durável, concorrência real, transação multi-instância, email, broker, pagamentos, autenticação ou garantia de entrega exatamente uma vez. A camada de Comunicações gera somente um DTO demonstrativo. Para falhas de entrega e outbox persistente, consulte o CERBERUS 03.
