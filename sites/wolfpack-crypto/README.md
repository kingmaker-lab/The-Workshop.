# WolfPack Crypto Lab — Site

Site de pesquisa em criptografia do ecossistema The Workshop, publicado em **https://wolfpack-crypto.pages.dev/**.

## Arquivo de experimentos

- [Experimentos 001–007](https://wolfpack-crypto.pages.dev/experimentos/)
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
