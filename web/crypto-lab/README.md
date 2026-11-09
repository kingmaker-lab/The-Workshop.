# Crypto Lab — The Workshop Labs

**Status:** EXP-001 e EXP-002 implementados, laboratórios educativos. Sem criptoativos ou operações financeiras.

Esta pasta contém um site estático para demonstrar **SHA-256, blocos encadeados e detecção de adulteração**. Abra com servidor HTTP local (Web Crypto exige contexto seguro; localhost é aceito), por exemplo `python3 -m http.server 8000` nesta pasta.

## Experimento
- EXP-001: criar até 12 blocos, calcular hashes SHA-256 e alterar um bloco antigo para observar divergências.
- EXP-002 (implementado em `pow/`): mineração PoW usando Web Worker, dificuldade 1–4 zeros hexadecimais, nonce, cancelamento, telemetria, verificação independente e limite de 500.000 tentativas por bloco (até cinco blocos).
- EXP-003 (planejado): chaves e assinaturas digitais.
- EXP-004 (planejado): modelo UTXO.
- EXP-005 (planejado): mempool e P2P.

**Limites:** não implementa consenso distribuído, assinaturas, ajuste automático de dificuldade nem garantias de integridade contra um adversário que controle a aplicação. Não constitui criptomoeda utilizável.

## Publicação
O projeto Cloudflare Pages `workshop-labs` usa fluxo de deploy independente. Apenas fazer commit no GitHub **não publica** esta página. Integre esta pasta ao pacote atual de publicação do Labs e inclua seu link no índice existente sem substituir outros arquivos. Faça preview, smoke tests e rollback conforme `docs/SECURITY_RELEASE_GATE.md`.

Arquivos sem dependências externas: `index.html`, `style.css`, `app.js`; EXP-002: `pow/index.html`, `pow/style.css`, `pow/app.js`, `pow/miner.worker.js`.

## Integração publicada (2026-11-03)

- Entrada no portal: https://workshop-labs.pages.dev/#blockchain-experiments
- Experimento interativo: https://workshop-labs.pages.dev/crypto-lab/
- Código do integration worker: `workshop-labs-integration-worker.js`
- Cloudflare Pages production deploy: `b321939a-d200-4bf9-b553-e1d28b6ae152`.
- Rollback anterior à integração: `104f1000-7823-4aae-94cd-fc85bba0702b` (ARGUS v0.3).

**Arquitetura temporária:** a integração foi entregue com Worker advanced mode que injeta a nova seção e responde às rotas `/crypto-lab/*`; as demais rotas fazem proxy transparente para o snapshot imutável `https://104f1000.workshop-labs.pages.dev`. Isso manteve Ouroboros e ARGUS no ar sem reempacotar o deploy atual, mas acopla o portal a um deployment antigo, aumenta um salto de rede e deve ser **substituído por um build completo e reproduzível**. **Não remova** esse snapshot nem faça rollback de deploys sem verificar as dependências. **Publicações futuras Direct Upload** precisam incorporar essa integração, senão o card de blockchain desaparecerá da página principal. O fluxo de manutenção deve incorporar o restante dos assets e functions do Labs em um pacote versionado, e executar smoke tests em todas as rotas antes de atualizar produção.

## EXP-002 publicado (2026-11-09)

- [Proof-of-Work Miner](https://workshop-labs.pages.dev/crypto-lab/pow/)
- [Documentação e testes](pow/README.md)
- Deploy de produção: `8bf689ec-7006-4e52-807d-b0ac402a0969`
- Rollback da versão anterior: `b321939a-d200-4bf9-b553-e1d28b6ae152`
- Smoke tests realizados no catálogo e na página de mineração; execução local de quatro testes do algoritmo.
- O código de integração mantém o snapshot anterior e as rotas já existentes. Não remova o snapshot original sem migrar o pacote completo.
