# The Workshop Labs — portal público

Fonte versionada do portal [workshop-labs.pages.dev](https://workshop-labs.pages.dev/), implantado como **Cloudflare Pages Direct Upload** com Advanced Worker `_worker.js` e sem dependências de build.

## Páginas e destinos

- `/`, `/index.html`: catálogo de cinco laboratórios.
- `/argus/`: documentação estática do ARGUS, preservada por este Worker.
- `/assets/labs.css`: folha de estilo de primeira parte.
- ARES: link para o diretório de código ARES no repositório, evitando um caminho interno que retornava 404.
- Crypto Lab: portal Cloudflare Pages independente.
- WolfPack OS: plataforma interativa independente.
- CERBERUS: [portal de arquitetura de software](https://cerberus.wolfpackworkshop.workers.dev/), com estudos 01–03 e ADRs. **Não é um gateway de segurança nem controla os outros aplicativos.**

## Segurança

- Zero JavaScript de cliente, nenhum formulário, iframe, proxy ou dados de usuários.
- CSP estrita no catálogo: `default-src 'none'`, `script-src 'none'`, `style-src 'self'`, sem estilos inline.
- Exceção de `style-src 'unsafe-inline'` restrita à rota legado `/argus/`, que mantém CSS inline.
- HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, COOP, CORP.
- `GET` e `HEAD` somente; 404 em caminhos não reconhecidos; 405 nos demais métodos.
- Segurança de outros domínios/aplicações fora do escopo deste Worker e requer testes separados.

## Testes e deploy

```bash
node --test web/workshop-labs/tests/smoke.test.mjs
npx wrangler pages deploy web/workshop-labs --project-name workshop-labs --branch main
```

A implantação por API do Cloudflare Pages exige `manifest` JSON e o arquivo `_worker.js`. Fazer snapshot do deployment atual, validar os testes e os links, publicar e repetir os smoke tests após o deploy. Evitar substituir a aplicação por HTML estático isolado: o `_worker.js` também atende `/argus/`.
