# The Workshop Labs — portal público

Fonte versionada do portal [workshop-labs.pages.dev](https://workshop-labs.pages.dev/), implantado como **Cloudflare Pages Direct Upload** com Advanced Worker `_worker.js` e sem dependências de build.

## Páginas e destinos

- `/`, `/index.html`: catálogo de cinco laboratórios.
- `/argus/`: laboratório estático expandido do ARGUS com arquitetura, sinais, cenário reproduzível, formatos, quick start, segurança e roadmap.\n- `argus/index.html`: fonte editorial da página ARGUS; cópia embutida em `const ARGUS_HTML` no Worker; teste CI exige correspondência literal.\n- `/heartai/`: laboratório HeartAI com Byte-BPE, embeddings e mapa de atenção causal, totalmente no navegador; independente do ARGUS.
- `/heartai/tokenizer.js`, `/heartai/embeddings.js`, `/heartai/attention.js`: três demonstradores locais, sem API e com CSP `connect-src 'none'`.
- `/assets/labs.css`: folha de estilo de primeira parte.
- ARES: link para o diretório de código ARES no repositório, evitando um caminho interno que retornava 404.
- Crypto Lab: portal Cloudflare Pages independente.
- WolfPack OS: plataforma interativa independente.
- CERBERUS: [portal de arquitetura de software](https://cerberus.wolfpackworkshop.workers.dev/), com estudos 01–03 e ADRs. **Não é um gateway de segurança nem controla os outros aplicativos.**

## Segurança

- O catálogo e o ARGUS não executam JavaScript de cliente, não usam formulários nem iframes e não coletam dados de usuários. A página HeartAI tem JavaScript local autorizado somente na sua própria rota.
- CSP estrita no catálogo: `default-src 'none'`, `script-src 'none'`, `style-src 'self'`, sem estilos inline.
- Exceção de `style-src 'unsafe-inline'` restrita às páginas ARGUS e HeartAI, que têm CSS inline. Em HeartAI há exceção específica de `script-src 'self'` e `connect-src 'none'`.
- HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, COOP, CORP.
- `GET` e `HEAD` somente; 404 em caminhos não reconhecidos; 405 nos demais métodos.
- Segurança de outros domínios/aplicações fora do escopo deste Worker e requer testes separados.

## Testes e deploy

```bash
node --test web/workshop-labs/tests/*.test.mjs
npx wrangler pages deploy web/workshop-labs --project-name workshop-labs --branch main
```

A implantação por API do Cloudflare Pages exige `manifest` JSON e o arquivo `_worker.js`. Fazer snapshot do deployment atual, validar os testes e os links, publicar e repetir os smoke tests após o deploy. Evitar substituir a aplicação por HTML estático isolado: o `_worker.js` também atende `/argus/`.

## Atualização editorial do ARGUS (30/10/2026)

O ARGUS tem agora uma página com navegação por âncoras, pipeline visual, detalhes das cinco famílias de sinais, exemplo didático de 17 eventos/3 alertas, formatos, configuração padrão, comandos locais, limitações de segurança e experimentos planejados. Todos os números descrevem **a versão de laboratório**, não uma API ativa ou serviço de monitoramento online. Para atualizar a página, edite `web/workshop-labs/argus/index.html` e sincronize a constante `ARGUS_HTML` em `web/workshop-labs/_worker.js` antes do deploy. `tests/argus-content.test.mjs` impedirá que as versões divirjam.

## HEART_005 (13/11/2026)

A pesquisa de atenção causal foi publicada no repositório como forward pass Python de uma cabeça (`IA/Heart/heart/neural/attention.py`) e como mapa de calor client-side em `/heartai/#attention`. O peso do navegador não é o modelo Python nem é treinado. A implementação exige sequência curta, não armazena prompts, não baixa pesos e não expõe os dados do runtime do HeartAI. O Worker precisa preservar todas as suas constantes (incluindo `HEARTAI_ATTENTION_JS`) ao fazer deploy.

## Blockchain & Crypto Experiments (19/11/2026)

- EXP-001: `/crypto-lab/` (encadeamento SHA-256 e detecção de adulteração).
- EXP-002: `/crypto-lab/pow/` (Proof-of-Work local no browser).
- EXP-003: `/crypto-lab/signatures/` (carteiras fictícias ECDSA P-256).
- EXP-004/005: UTXO e P2P planejados, não implementados.

O Worker do Workshop Labs incorpora as rotas do `web/crypto-lab/workshop-labs-integration-worker.js` sem proxy ao snapshot legado, junto com o catálogo Blockchain. Testar `tests/blockchain-routes.test.mjs` e as rotas de ARGUS, HeartAI, NEXUS, Ouroboros e CERBERUS antes de publicar.

## NEXUS-06 EXP-009 — relatório estático (23/11/2026)

- Nova rota aditiva `/nexus/exp009/`, com página-fonte em `nexus/exp009/index.html` e CSS de primeira parte `nexus/exp009/report.css`.
- A página `/nexus/` conserva todo o seu conteúdo histórico e acrescenta somente um link para o novo relatório.
- Os números apresentados são derivados de saídas de terminal fornecidas pelo pesquisador, não de JSONs brutos verificados pelo site. O EXP-009 utiliza séries sintéticas e não prova generalização ou detecção operacional.
- Para atualizar o conteúdo de NEXUS ou EXP-009, sincronizar as constantes `NEXUS_HTML`, `NEXUS_EXP009_HTML` e `NEXUS_EXP009_CSS` dentro do advanced Worker `_worker.js`.
- Segurança: nenhuma dependência client-side, `script-src 'none'`, `connect-src 'none'`, estilos somente da origem, 405 para métodos não GET/HEAD, HSTS, nosniff, anti-framing e cache limitado; verificar com `node --test web/workshop-labs/tests/*.test.mjs`.
- Arquivos locais de métricas/modelos e quaisquer fontes de dados privadas **não** são publicados.
- Não remover nem sobrescrever `/argus/`, `/heartai/`, `/nexus/`, `/crypto-lab/` e seus assets, páginas originais nem o snapshot histórico legado.

## ARGUS v0.5 — correlação temporal multi-host (24/11/2026)

O portal /argus/ recebeu uma seção *aditiva* `#multihost`, com linha do tempo de oito eventos fictícios e explicação do engine local opt-in `argus/detection/multihost_v05.py`. Regras Sigma, watcher v0.3 e seções v0.4 permanecem. O HTML de `argus/index.html` deve continuar literalmente sincronizado à constante `ARGUS_HTML` do advanced Worker. Nenhum payload de usuário, modelo, regra importada ou API de detecção foi publicado.

Testar `argus/tests/test_multihost_v05.py`, `web/workshop-labs/tests/argus-v05.test.mjs`, as suítes históricas, CSP/GET/HEAD/404/405 e a navegação NEXUS/HeartAI/Crypto Lab/CERBERUS antes de qualquer deploy. O CSS legado da página ARGUS ainda tem uma exceção de `style-src 'unsafe-inline'`; scripts, fetch e iframes continuam proibidos. O teste de segurança completo de ambiente local ou da infraestrutura de borda não é substituído por esses controles.
