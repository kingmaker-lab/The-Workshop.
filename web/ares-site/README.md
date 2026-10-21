# The Workshop Labs — Site / Portal

**Build. Break. Understand. Rebuild.**

O site principal é a porta de entrada para os laboratórios do The Workshop.

## Endereços

| Rota | Destino | Descrição |
| --- | --- | --- |
| [workshop-labs.pages.dev](https://workshop-labs.pages.dev/) | Portal / hub | Diretório dos projetos |
| [/projects/wolf-vm/](https://workshop-labs.pages.dev/projects/wolf-vm/) | WOLF-VM | Página técnica do interpretador em C11 (sem execução remota de bytecode) |
| [/projects/ares/](https://workshop-labs.pages.dev/projects/ares/) | ARES | Página técnica do servidor HTTP em C |
| [/projects/ares/responses-routing/](https://workshop-labs.pages.dev/projects/ares/responses-routing/) | ARES v0.3 | Servidor HTTP local integrado, testes e segurança |
| [/projects/ares/static-files/](https://workshop-labs.pages.dev/projects/ares/static-files/) | ARES v0.4 | Static files, MIME, traversal testing e check-up |
| [/projects/crypto/](https://workshop-labs.pages.dev/projects/crypto/) | Crypto Labs | Redireciona para o projeto Crypto |
| [wolfpack-crypto.pages.dev](https://wolfpack-crypto.pages.dev/) | Crypto Labs | Site próprio de estudos e experimentos de criptografia |

O ARES está **em desenvolvimento**. O terminal na página é uma demonstração conceitual; não significa que exista um servidor HTTP escrito em C atendendo requisições públicas.

## Fontes do site

- `hub.html`: conteúdo da home / hub.
- `hub.css`: estilo da home.
- `tcp-foundation.html` e `tcp.css`: documentação/estilos da v0.1.
- `http-parser.html` e `http-parser.css`: documentação/estilos da v0.2.
- `responses-routing.html`: documentação técnica da v0.3.
- `static-files.html`: documentação técnica da v0.4.
- `tests/security.test.mjs`: regressões de segurança do Pages Worker (Node 22).
- `_worker.js`: Cloudflare Pages Advanced Mode — contém o hub, a página do ARES e o roteamento.

A versão publicada do hub está incorporada em `_worker.js`. Após editar os arquivos-fonte do hub, sincronize suas alterações com as constantes `HUB_HTML` e `HUB_CSS` do Worker antes do deploy.

## Rotas do Pages Worker

- `/` → home dos laboratórios
- `/projects/wolf-vm/` e `/wolf-vm/` → WOLF-VM v0.1 (documentação estática)
- `/projects/ares/` e `/ares/` → ARES
- `/projects/ares/tcp-foundation/` → TCP Foundation v0.1
- `/projects/ares/responses-routing/` → Responses & Routing v0.3
- `/projects/ares/static-files/` → Static Files v0.4
- `/projects/ares/http-parser/` → HTTP Parser v0.2
- `/projects/crypto/`, `/crypto/`, `/crypto-labs/` → redirecionamento ao Crypto Labs
- `/assets/hub.css`, `/assets/ares.css`, `/assets/tcp.css`, `/assets/http-parser.css`, `/assets/ares.js`, `/favicon.svg` → recursos locais

## Deploy

No Cloudflare Pages, utilize o projeto existente `workshop-labs` e publique um diretório contendo `_worker.js` na raiz via Direct Upload. O Worker serve HTML e CSS, sem dependências externas.

**Importante:** Pages hospeda a apresentação do ARES, não o executável C17/POSIX. O servidor HTTP do ARES precisará de um host Linux separado, de auditoria e de uma configuração segura antes de qualquer implantação de produção.

## Mandatory website security regression

    node --test web/ares-site/tests/security.test.mjs

This checks GET/HEAD, 404/405, redirect target, content types, restrictive script CSP, framing/other security headers, safe external links and static input handling. Additional checklists are in docs/SECURITY_RELEASE_GATE.md. The current site CSP allows inline *styles* for existing markup; it does **not** allow inline JavaScript. Eliminating inline CSS is a future hardening task.

## v0.4 security review

O servidor C não é executado pelo Cloudflare Pages. A nova página documenta controles de filesystem e o risco residual. Check-up em docs/security-reviews/ares-v0.4-2026-10-19.md. Rode os testes de website antes e depois do deploy: node --test web/ares-site/tests/security.test.mjs. 
