# ADR-0002 — Inverter dependências para preservar o core

- **Data:** 2026-10-21
- **Estado:** adotado para este experimento educacional; sujeito a reavaliação
- **Escopo:** estudo de reservas simples em Python 3.11+.

## Contexto
Ao substituir persistência em memória por SQLite ou transportar comandos por CLI em vez de JSON, queremos evitar alterações nas regras de negócio. Arquitetura em camadas sem regra explícita pode fazer casos de uso importarem drivers.

## Decisão
- Domínio com invariantes e entidades imutáveis.
- Aplicação coordena casos de uso.
- Portas abstratas `ReservationRepository` e `IdGenerator` pertencem ao core.
- Adapters concretos: memória, SQLite, UUID4, CLI e controller JSON (sem listener HTTP).
- Dependências do código apontam para o core; composição ocorre fora dele.
- Implementações são verificadas por testes de contrato, unidade e regra de imports.

## Alternativas
1. **Active Record direto no caso de uso:** menos arquivos, maior acoplamento ao ORM/driver.
2. **Service Locator global:** flexível em aparência, porém torna dependências ocultas e testes menos previsíveis.
3. **Ports & Adapters com composição explícita (escolhida):** mais abstração e arquivos, menor efeito cascata nas políticas internas.

## Consequências
- Positivo: substituição de adapter e entrada preserva classes de domínio/usecase.
- Negativo: custo extra de interfaces, fixture, composição e organização. Para um CRUD trivial, isso pode ser complexidade desnecessária.
- Incerteza: testes não demonstram ganho de performance nem melhoria absoluta da manutenção sob equipes reais.

## Evidência esperada
Testes automatizados em dois repositórios e duas interfaces; inspeção de dependência do core. Sem benchmarks declarados.
