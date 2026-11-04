# WolfPack Crypto Lab — Site

Site de pesquisa em criptografia do ecossistema The Workshop, publicado em **https://wolfpack-crypto.pages.dev/**.

## Arquivo de experimentos

- [Experimentos 001–014](https://wolfpack-crypto.pages.dev/experimentos/)
- [001 — Reversibilidade Feistel](https://wolfpack-crypto.pages.dev/experimentos/001/)
- [002 — Análise diferencial](https://wolfpack-crypto.pages.dev/experimentos/002/)
- [003 — DDT de 8 bits](https://wolfpack-crypto.pages.dev/experimentos/003/)
- [004 — Ciclos, Floyd e Brent](https://wolfpack-crypto.pages.dev/experimentos/004/)
- [005 — Sensibilidade às condições iniciais](https://wolfpack-crypto.pages.dev/experimentos/005/)
- [006 — Bacias de atração](https://wolfpack-crypto.pages.dev/experimentos/006/)
- [007 — Strict Avalanche Criterion (piloto)](https://wolfpack-crypto.pages.dev/experimentos/007/)

Fonte dos experimentos: [Ouroboros Low Level](../../research/cryptography/ouroboros-low-level/README.md). Os EXP 004–006 incluem documentação e scripts reproduzíveis no GitHub. Os EXP 001–003 são fundamentos e provas conceituais; o EXP 007 está em fase piloto de SAC/BIC. Nenhum dos experimentos constitui auditoria de primitiva criptográfica.

## Arquitetura

O arquivo `worker.mjs` é um **Cloudflare Pages Worker (Advanced Mode)** autocontido. Ele gera páginas HTML estáticas, entrega recursos internos `/assets/style.css` e `/assets/site.js`, serve páginas de experimentos e retorna HTTP 404 para rotas desconhecidas.

O site usa apenas **JavaScript nativo do navegador** e não coleta senhas, seeds ou dados do laboratório. O SHA-256 Playground usa `crypto.subtle.digest()`. A DDT é calculada localmente e emprega apenas entradas demonstrativas.

## Segurança

- CSP restritiva: somente scripts e estilos da própria origem, sem `unsafe-inline` ou `unsafe-eval`.
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY` e `frame-ancestors 'none'`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy` bloqueando câmera, microfone, geolocalização e pagamentos.
- `GET/HEAD` apenas; demais métodos respondem 405.
- Nenhum endpoint de processamento remoto de entradas do usuário.

**Limite do check-up:** validação estática e status de implantação não substituem um teste HTTP real ou uma auditoria independente.

## Publicação manual pelo Wrangler

A implantação atual foi feita via API de deploy do Cloudflare Pages. O projeto não está conectado a um pipeline GitHub automático. Para novos deploys utilizando o arquivo versionado:

```bash
mkdir -p dist
cp worker.mjs dist/_worker.js
npx wrangler pages deploy dist --project-name wolfpack-crypto
```

Requer autenticação em uma conta Cloudflare com acesso ao projeto. O comando usa o `_worker.js` no formato de Advanced Mode e mantém a lógica de rotas no próprio arquivo.

## Observação científica

**Ouroboros é uma pesquisa autoral e experimental.** Os experimentos de SHA-256 truncado em 16/32 bits não representam uma prova de segurança do SHA-256 completo nem do motor C/Assembly. Não utilize essas construções para proteger informação sensível.

**Build. Break. Understand. Rebuild.**


- 008 — Cifra Feistel reduzida — implementação, testes e resultados em [Ouroboros EXP-008 no GitHub](https://github.com/kingmaker-lab/The-Workshop./tree/exp-008-reduced-feistel/research/cryptography/ouroboros-low-level/experiments/008-reduced-feistel).
- [009 — Análise diferencial e linear](https://wolfpack-crypto.pages.dev/experimentos/009/) — DDT e LAT completas da função de rodada do EXP-008, com enumeração exata e limites explícitos de interpretação. [Código e resultados](https://github.com/kingmaker-lab/The-Workshop./tree/exp-009-round-function-analysis/research/cryptography/ouroboros-low-level/experiments/009-round-function-analysis).


## Integração de pesquisa EXP-010 a EXP-014 (2026-11-04)

As novas páginas foram adicionadas ao Worker existente, sem substituir as rotas, os assets, o playground, a seção Low Level ou os cabeçalhos de segurança anteriores:

- [010 — Multi-round Feistel Trail Analysis](https://wolfpack-crypto.pages.dev/experimentos/010/)
- [011 — Differential Trails & Linear Hulls](https://wolfpack-crypto.pages.dev/experimentos/011/)
- [012 — KS1 Key Schedule Analysis](https://wolfpack-crypto.pages.dev/experimentos/012/)
- [013 — Related-Key Dependency & Cross-Round Analysis](https://wolfpack-crypto.pages.dev/experimentos/013/)
- [014 — Research Consolidation & Independent Conformance](https://wolfpack-crypto.pages.dev/experimentos/014/)

As cinco entradas também aparecem na página inicial e no arquivo de experimentos. As páginas 010–014 apresentam escopo, método, limites científicos, código e links de CI, sem afirmar que estimativas Markov são distribuições fixas, que estatísticas amostrais provam independência, ou que testes funcionais certificam segurança criptográfica.

### Validação e publicação

- Branch de integração: `crypto-lab-exp014-rollup`.
- Source alterado: somente `sites/wolfpack-crypto/worker.mjs` (páginas e navegação aditivas) e este README; teste de smoke e workflow novos foram acrescentados.
- Rotas antigas e os assets `/assets/style.css` e `/assets/site.js` são preservados.
- A página continua em Cloudflare Pages Advanced Mode; o upload de preview/produção usa o campo `_worker.js` do projeto `wolfpack-crypto`.
- Deployment de produção anterior, preservado como rollback: `647b3b38-a68e-4a66-a693-098edaa40972`.
- Não confundir o estado Assembly de 64 bits com a cifra Feistel de 16 bits EXP-008.
