# The Workshop Labs — portal público

Fonte versionada do portal [workshop-labs.pages.dev](https://workshop-labs.pages.dev/), implantado como **Cloudflare Pages Direct Upload** com Advanced Worker `_worker.js` e sem dependências de build.

## Páginas e destinos

- `/`, `/index.html`: catálogo de cinco laboratórios.
- `/argus/`: laboratório estático expandido do ARGUS com arquitetura, sinais, cenário reproduzível, formatos, quick start, segurança e roadmap.\n- `argus/index.html`: fonte editorial da página ARGUS; cópia embutida em `const ARGUS_HTML` no Worker; teste CI exige correspondência literal.\n- `/heartai/`: laboratório HeartAI com tokenizer e embeddings locais no navegador; independente do ARGUS.
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
