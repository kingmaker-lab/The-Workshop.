# ARES Site — The Workshop

Landing page do projeto **ARES** no Cloudflare Pages.

- URL: https://workshop-labs.pages.dev/
- Alias: https://workshop-labs.pages.dev/projects/ares/
- Arquivo de implantação: \`_worker.js\` (Cloudflare Pages Advanced Mode).
- Stack: HTML, CSS e JavaScript sem dependências.
- O projeto ARES ainda está em desenvolvimento. O exemplo de terminal é uma **simulação conceitual**, não um servidor C em execução.

## Desenvolvimento local

Use Wrangler com o arquivo \`_worker.js\` em um diretório de output do Pages; ou faça uma requisição ao Worker por meio do ambiente local suportado pelo Wrangler.

## Deploy

No Cloudflare Pages, projeto \`workshop-labs\`, faça Direct Upload de um diretório contendo \`_worker.js\` na raiz. O ambiente de produção responde aos caminhos \`/\`, \`/ares/\` e \`/projects/ares/\`.

Não confundir a landing page (Cloudflare Pages) com o futuro servidor HTTP escrito em C, que precisará de um host Linux separado para executar sockets POSIX.
