# 🐺 CERBERUS — Software Architecture Lab

> **Build. Break. Understand. Rebuild.**

**Cerberus é o módulo de arquitetura de software do The Workshop.** Investigamos estruturas, fronteiras, padrões e decisões arquiteturais através de estudos comparativos e experimentos reproduzíveis. **Não é** um sistema de orquestração, um gateway de autenticação, um produto de governança, nem o hub oficial dos demais projetos.

## Trilha de pesquisa

| Ciclo | Tema | Situação |
|---|---|---|
| CERBERUS 01 | Fundamentos, atributos de qualidade, acoplamento, coesão, trade-offs | estudo introdutório publicado |
| CERBERUS 02 | Arquitetura em camadas, Clean Architecture, Hexagonal | estudo e código disponíveis |
| CERBERUS 03 | Monólitos modulares, microsserviços e sistemas distribuídos | planejado |
| CERBERUS 04 | SOLID, design patterns, DDD, C4 e ADRs | planejado |
| CERBERUS 05 | Resiliência, escalabilidade, observabilidade, performance e segurança por design | planejado |

## Método

**Contexto → Hipótese → Alternativas → Implementação → Métricas → Decisão (ADR).**

Não adotaremos dogmas arquiteturais. Cada experimento deverá declarar requisitos, restrições, limites conhecidos, dados observados e critérios de decisão. Um protótipo não é evidência definitiva de escalabilidade ou segurança.

## Primeira bancada: CERBERUS 01 — monólito modular versus microsserviços

Cenário hipotético: serviço de reservas, equipe de três pessoas, orçamento limitado, baixa escala inicial. Escolha arquitetural é documentada como **hipótese condicionada ao contexto**. O experimento propõe métricas de latência p95, falhas, custo de operação e complexidade de deploy. A página não alega que esses números já foram medidos.

- Página: https://cerberus.wolfpackworkshop.workers.dev/labs/01
- Documento: [ADR 0001](docs/ADR-0001-modular-monolith.md).
- Portal: https://cerberus.wolfpackworkshop.workers.dev/


## Segunda bancada: CERBERUS 02 — Camadas, Clean & Hexagonal

Pergunta: o mesmo caso de uso de reservas pode trocar o adaptador SQLite pelo adaptador de memória sem modificar as regras de negócio?

- Página: https://cerberus.wolfpackworkshop.workers.dev/labs/02
- Fonte e testes: [02-layers-clean-hexagonal](experiments/02-layers-clean-hexagonal/).
- Decisão: [ADR 0002](experiments/02-layers-clean-hexagonal/docs/ADR-0002-ports-and-adapters.md).
- Comandos: `cd Cerberus/experiments/02-layers-clean-hexagonal && python -m pip install -e . && python -m unittest discover -s tests -v`.
- Python >= 3.11; biblioteca padrão como dependência em runtime. Nenhum servidor HTTP nem banco de dados público são iniciados.
- Segurança: experimento local sem autenticação, autorização ou controle de capacidade real. Não usar dados pessoais reais.


## Terceira bancada em desenvolvimento: CERBERUS 03 — fronteiras de entrega

Parte 1 em branch de pesquisa: [simulação de entrega e falhas](experiments/03-delivery-boundaries/). Dois modelos locais de reservas/notificações permitem testar entrega duplicada após falha de confirmação e deduplicação no consumidor, com casos de falha determinísticos.

- Código e testes: [03-delivery-boundaries](experiments/03-delivery-boundaries/).
- Decisão: [ADR-0003](experiments/03-delivery-boundaries/ADR-0003-delivery-boundary.md).
- Execução: `cd Cerberus && npm test` (Node.js >= 20).
- Limite: ambos os modelos são **simulações em memória**, sem rede, broker ou persistência real. Não há benchmark de microsserviços nem mudança de deploy.

## Implementação pública

Worker independente com HTML e CSS estáticos, sem JavaScript executado no cliente, sem cookies, sem bindings de acesso a serviços e sem proxy. Publicação não altera os deploys do Workshop Labs, Ares, Crypto Lab ou WolfPack OS.

- `/` — página principal do laboratório.
- `/labs/01` — primeiro estudo.
- `/labs/02` — segundo estudo com fonte executável, contratos e ADR.
- `/api/status` — status **do portal**, não dos demais serviços.
- `/api/modules` — trilha de módulos (somente leitura).
- `/api/projects` — catálogo anterior mantido exclusivamente por compatibilidade.

## Segurança e testes

- Modelagem: [docs/SECURITY.md](docs/SECURITY.md)
- Arquitetura: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Testes do portal: `cd Cerberus && npm test` (Node.js >= 20).
- Testes do experimento 02: `cd Cerberus/experiments/02-layers-clean-hexagonal && python -m unittest discover -s tests -v` após instalar o pacote.
- Deploy: publicar `Cerberus/worker.js` no Worker `cerberus` com alterações versionadas e revisão de headers, disponibilidade e regressões.

**Atenção:** `web/workshop-labs/_worker.js` é um protótipo antigo, não é o código de produção do Workshop Labs e não deve ser implantado em substituição ao portal existente.
