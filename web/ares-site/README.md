# The Workshop Labs — Site / Portal

**Build. Break. Understand. Rebuild.**

O site principal é a porta de entrada para os laboratórios do The Workshop.

## Endereços

| Rota | Destino | Descrição |
| --- | --- | --- |
| [workshop-labs.pages.dev](https://workshop-labs.pages.dev/) | Portal / hub | Diretório dos projetos |
| [/projects/ares/](https://workshop-labs.pages.dev/projects/ares/) | ARES | Página técnica do servidor HTTP em C |
| [/projects/crypto/](https://workshop-labs.pages.dev/projects/crypto/) | Crypto Labs | Redireciona para o projeto Crypto |
| [wolfpack-crypto.pages.dev](https://wolfpack-crypto.pages.dev/) | Crypto Labs | Site próprio de estudos e experimentos de criptografia |

O ARES está **em desenvolvimento**. O terminal na página é uma demonstração conceitual; não significa que exista um servidor HTTP escrito em C atendendo requisições públicas.

## Fontes do site

- `hub.html`: conteúdo da home / hub.
- `hub.css`: estilo da home.
- `tcp-foundation.html` e `tcp.css`: documentação/estilos da v0.1.
- `http-parser.html` e `http-parser.css`: documentação/estilos da v0.2.
- `_worker.js`: Cloudflare Pages Advanced Mode — contém o hub, a página do ARES e o roteamento.

A versão publicada do hub está incorporada em `_worker.js`. Após editar os arquivos-fonte do hub, sincronize suas alterações com as constantes `HUB_HTML` e `HUB_CSS` do Worker antes do deploy.

## Rotas do Pages Worker

- `/` → home dos laboratórios
- `/projects/ares/` e `/ares/` → ARES
- `/projects/ares/tcp-foundation/` → TCP Foundation v0.1
- `/projects/ares/http-parser/` → HTTP Parser v0.2
- `/projects/crypto/`, `/crypto/`, `/crypto-labs/` → redirecionamento ao Crypto Labs
- `/assets/hub.css`, `/assets/ares.css`, `/assets/tcp.css`, `/assets/http-parser.css`, `/assets/ares.js`, `/favicon.svg` → recursos locais

## Deploy

No Cloudflare Pages, utilize o projeto existente `workshop-labs` e publique um diretório contendo `_worker.js` na raiz via Direct Upload. O Worker serve HTML e CSS, sem dependências externas.

**Importante:** Pages hospeda a apresentação do ARES, não o executável C17/POSIX. O servidor HTTP do ARES precisará de um host Linux separado, de auditoria e de uma configuração segura antes de qualquer implantação de produção.
