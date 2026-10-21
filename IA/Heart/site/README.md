# ARGUS Protocol — HeartAI / Public Lab

**Publicado em produção:** https://workshop-labs.pages.dev/argus/

O ARGUS é a bancada de pesquisa em inteligência artificial do The Workshop. Seu primeiro projeto é **HeartAI (PROJECT_001)**.

## Source of truth para a publicação

- `IA/Heart/site/argus/index.html`: HTML e apresentação do laboratório.
- `IA/Heart/site/argus/argus.js`: demonstração de tokenização sem rede.
- `web/ares-site/_worker.js`: **Worker avançado do projeto Cloudflare Pages `workshop-labs`**; agrega a homepage, ARES, WOLF-VM, ARGUS e seus assets.
- `/argus/` e `/argus/heartai/`: páginas públicas (equivalentes); `/argus/argus.js`: recurso JS sob a mesma origem.

**Importante:** o projeto usa **Direct Upload**, sem publicação automática a partir de commits no GitHub. Para atualizar o site, é necessário recriar o deploy completo usando o `_worker.js` agregado e promover o resultado após testar em preview. Não envie apenas a página ARGUS: isso substituiria o deploy existente e apagaria rotas dos outros projetos.

## Recursos e limites

O playground utiliza um corpus fixo de demonstração e realiza merges Byte-BPE no navegador. **Não executa o runtime Python**, não carrega memórias reais, não consulta APIs externas e não representa treinamento de um modelo de linguagem. A memória SQLite e as ferramentas operacionais permanecem privadas.

A aplicação de Pages mantém CSP restritiva e serve o script por rota própria (`script-src 'self'`).

## Registro de publicação

- Data: 2026-10-21.
- Pages: `workshop-labs`.
- Deploy de produção: `d6ee7429-75bd-4b76-9f0e-a9847812919f`.
- Status confirmado pela API Cloudflare: `deploy / success`.
- Preview validado pela API: `96b3b38b-d09b-4cb5-a2a1-fb2a3d9bd7fd` (`deploy / success`).
- Teste local de rotas do Worker: homepage, ARGUS, playground, ARES, WOLF-VM, 404 e método POST bloqueado.
- Validação HTTP pública a partir desta sessão: **não confirmada**, pois o leitor web forneceu conteúdo cacheado anterior à publicação.

No caso de problema em produção, use o mecanismo de rollback para o último deploy conhecido como estável.
