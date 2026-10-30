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
