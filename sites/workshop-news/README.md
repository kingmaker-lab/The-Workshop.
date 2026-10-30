# 📰 Workshop News | The Workshop

**Portal experimental de notícias e inteligência tecnológica.**

## Conteúdo

- Notícias técnicas do Hacker News (via API Algolia) e feeds públicos dos blogs oficiais Cloudflare e GitHub.
- Atualizações do The Workshop provenientes **exclusivamente dos commits públicos do GitHub**.
- Cards para os demais laboratórios: Workshop Labs, Crypto Lab, WolfPack OS e Cerberus.
- Filtros por Segurança, IA, Dev e Infra, com busca local.
- Interface responsiva e acessível. Sem publicidade, cadastro, cookies próprios ou bibliotecas externas de front-end.

## Projeto Cloudflare Pages

Cloudflare Pages **Advanced Mode** com `_worker.js`. O Worker permite somente `GET` e `HEAD`, responde às rotas `/api/feed`, `/`, `/index.html`, `/styles.css`, `/app.js` e `/favicon.svg`, e delega arquivos estáticos ao binding `env.ASSETS`.

A API faz requisições apenas a quatro fontes predeterminadas. A atualização é cacheável na borda por 300 segundos; se alguma fonte cair, a API responde com resultado parcial e a interface indica a condição. Não há parâmetro que permita mudar a URL acessada pelo servidor.

As fontes são apresentadas com links e atribuição; o conteúdo externo é renderizado com `textContent`, não com `innerHTML`. Dados do GitHub são movimentos de código, **não comunicados editoriais oficiais**.

## Testar

```bash
node --test sites/workshop-news/tests/*.test.mjs
node sites/workshop-news/scripts/build.mjs
```

Não exige dependências NPM.

## Publicação controlada

Depois que CI e revisão de segurança forem aprovados:

```bash
node sites/workshop-news/scripts/build.mjs
npx wrangler pages deploy sites/workshop-news/dist --project-name workshop-news
```

O diretório `dist` contém **apenas cinco arquivos necessários à publicação**. Não implante a raiz da pasta; ela contém testes e documentação. A integração com GitHub e o deploy automatizado em produção não estão configurados nesta versão.

## Modelo de ameaças e limites

- Não há credenciais, login, banco de dados, upload, busca remota parametrizada, nem execução de código recebido da internet.
- Conexões externas do servidor usam fontes fixas, HTTPS, timeout e limite de tamanho para respostas.
- CSP `script-src 'self'`, `object-src 'none'`, `frame-ancestors 'none'`, HSTS, `nosniff`, `Referrer-Policy: no-referrer` e `Permissions-Policy`.
- Respostas 404/405 têm `Cache-Control: no-store`.
- Fontes externas podem ficar indisponíveis, mudar o schema, ter limites de API ou publicar erros e desinformação. Não representamos a curadoria como verificação factual.
- News não é um SOC, não possui SLA de detecção, nem é uma fonte exclusiva para incidentes. Para decisões críticas, confira a fonte primária.
- Taxas e quotas dependem dos provedores. Analise uso real, logs e CDN antes de tráfego elevado.
- Em produção, validar cabeçalhos HTTP, CSP, acessibilidade e comportamento da interface no navegador.

## Próximo ciclo

1. Curadoria editorial opcional com revisão humana e links para publicações do Workshop.
2. Status operacional real de serviços, se disponível via monitoramento autenticado e controlado.
3. Histórico e categorias persistentes, com testes contra notícias duplicadas e fontes degradadas.
4. Instrumentação mínima de saúde com política de privacidade clara.

**Build. Break. Understand. Rebuild.**

## Implantação real — 30/10/2026

- **Produção:** https://workshop-news.pages.dev/
- **Cloudflare Pages:** projeto `workshop-news`, branch de publicação `main`, método **Direct Upload**.
- **Deployment ID:** `6a5d84a6-ad37-4ec1-b685-b30b51417e6e` (status Cloudflare: `success`).
- **Fonte:** branch `feat/workshop-news-portal-20261030`, commit `c4c83082e6fea106cee79d5b0018fcbf455fe04e`.
- **Empacotamento realizado:** Worker único contendo os quatro assets estáticos incorporados. A aplicação usa roteamento interno para responder HTML/CSS/JS/SVG; não depende do binding `env.ASSETS` neste deployment específico. A fonte versionada permanece modular e o build Wrangler produz os cinco arquivos separadamente.
- **Verificação ao vivo:** navegador Cloudflare abriu a homepage, executou o JavaScript, exibiu 18 notícias e histórico de commits, e o endpoint `/api/feed` retornou artigos e atualizações.
- **Estado das fontes:** 3 de 4 disponíveis na verificação (Hacker News, Cloudflare Blog e GitHub commits); GitHub Blog indisponível naquele ciclo. O portal apresenta `FONTES PARCIAIS` corretamente.
- **Limites:** respostas HTTP/cabeçalhos, análise de acessibilidade visual, CSP em navegador e todos os casos 404/405 ainda exigem verificação dedicada em produção. Não há sincronização automática GitHub → Cloudflare; cada nova versão exige deploy manual.


## Atalho: Jogos Interativos

- No portal, o menu **Jogos Interativos** e seu card no ecossistema abrem `/jogos`.
- `GET /jogos`, `GET /jogos/` e `HEAD` devolvem `302 Location: https://wolfpack.wolfpackworkshop.workers.dev/`.
- O destino é fixo; parâmetros de query não são propagados e outros métodos continuam 405.
- Esse atalho não incorpora os jogos ao portal nem cria proxy, iframe ou nova API.

### Publicação do atalho Jogos Interativos — 30/10/2026

- Rota: `https://workshop-news.pages.dev/jogos` (302 para `https://wolfpack.wolfpackworkshop.workers.dev/`).
- Deploy Cloudflare Pages (produção): `55bd886e-e9da-4807-a659-cff34278f848`; origem do build: commit `b4d2254564803fe8738c0c40301625184233b0cd`.
- Testes CI para a versão de origem: **success**; homepage publicada contém dois atalhos `/jogos`.
- A verificação direta do cabeçalho `Location` em produção ainda não foi concluída; o navegador Cloudflare atingiu um limite temporário de requisições (HTTP 429). O destino fixo e o status 302 foram cobertos por testes de código.


## Atualização editorial — 30/10/2026

### Fresco da bancada
A seção de destaques informa estágio e fonte verificável para:
- **Ouroboros EXP-008:** pesquisa Feistel didática, oito rodadas e análise de um bit para três chaves; não usar para dados reais.
- **Protocolo Ruby:** backend de *staging* somente leitura no diretório `protocolo-ruby/render`. Isto não significa backend público em produção.
- **Security Hardening:** validações de segurança em revisão no PR #10.
- **Jogos Interativos:** atalho /jogos já publicado para WolfPack OS.

A atividade recente combina os commits de `main` com as branches experimentais `feature/protocolo-ruby-v0.1` e `exp-008-reduced-feistel`. Os feeds de branches são opcionais e nunca aumentam indevidamente a contagem das quatro fontes base. Datas e estados das quatro notas editoriais são estáticos e precisam de nova revisão para futuras mudanças; os commits são carregados dinamicamente. Um feed externo indisponível não remove as notas verificadas.

O diretório público continua limitado a HTML, CSS, JS, SVG e o Worker. Antes de cada publicação, executar o workflow Workshop News, validar o estado dos destaques e testar o carregamento da rota /api/feed no site ao vivo.
