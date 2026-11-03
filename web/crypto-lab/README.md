# Crypto Lab — The Workshop Labs

**Status:** EXP-001, demonstração educativa. Sem criptoativos ou operações financeiras.

Esta pasta contém um site estático para demonstrar **SHA-256, blocos encadeados e detecção de adulteração**. Abra com servidor HTTP local (Web Crypto exige contexto seguro; localhost é aceito), por exemplo `python3 -m http.server 8000` nesta pasta.

## Experimento
- EXP-001: criar até 12 blocos, calcular hashes SHA-256 e alterar um bloco antigo para observar divergências.
- EXP-002 (planejado): mineração PoW com dificuldade e limite de trabalho.
- EXP-003 (planejado): chaves e assinaturas digitais.
- EXP-004 (planejado): modelo UTXO.
- EXP-005 (planejado): mempool e P2P.

**Limites:** não implementa consenso distribuído, assinaturas, mineração, ajuste de dificuldade nem garantias de integridade contra um adversário que controle a aplicação. Não constitui criptomoeda utilizável.

## Publicação
O projeto Cloudflare Pages `workshop-labs` usa fluxo de deploy independente. Apenas fazer commit no GitHub **não publica** esta página. Integre esta pasta ao pacote atual de publicação do Labs e inclua seu link no índice existente sem substituir outros arquivos. Faça preview, smoke tests e rollback conforme `docs/SECURITY_RELEASE_GATE.md`.

Arquivos sem dependências externas: `index.html`, `style.css`, `app.js`.
