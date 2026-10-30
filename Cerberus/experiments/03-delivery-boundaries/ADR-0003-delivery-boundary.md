# ADR-0003 — Estudar a fronteira de mensagens antes de distribuir

- Estado: **proposta experimental**, não decisão universal
- Data: 2026-10-30
- Escopo: CERBERUS 03, Parte 1

## Contexto

A primeira bancada avaliou monólito modular e microsserviços por requisitos. A segunda demonstrou portas e adaptadores. O terceiro ciclo investiga o custo semântico de separar operações, começando pela entrega de eventos de reservas para notificações.

## Alternativas

1. **Chamada local síncrona.** Fluxo simples e observável, mas acopla a duração e a falha de notificação ao processo de reservar.
2. **Entrega via evento com outbox.** Permite eventual processamento assíncrono, mas exige controlar tentativas, confirmação, deduplicação e estados intermediários.

## Escolha para a bancada

Implementar dois modelos **em memória** e injetar falhas determinísticas em torno da entrega e da confirmação. Tratar idempotência como obrigação do consumidor neste exemplo.

## Evidência exigida

- Repetição do mesmo comando não cria outra reserva.
- Falha antes da entrega mantém o evento pendente.
- Falha após o efeito e antes do ack exige repetição.
- Repetição não duplica o efeito do consumidor idempotente.
- Scripts de teste devem passar em Node 20+ sem dependências externas.

## Limites e próximos gatilhos

Nenhum modelo usa transação persistente, rede, broker, autenticação, concorrência real ou duas instâncias isoladas. O experimento **não** demonstra que microsserviços são mais confiáveis. A próxima decisão depende de testes com persistência, timeouts, crash/restart e métricas observadas.
