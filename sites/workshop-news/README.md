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


### Release Workshop News: novidades da bancada (30/10/2026)

- Cloudflare Pages `workshop-news`: produção atualizada, deployment `2071d8f9-99fd-4794-8249-add98448af72`, status **success**.
- Origem da aplicação: commit `bbd02104fb72edf513351499a2cab72d4fef3556` da branch `feat/workshop-news-portal-20261030` (CI Workshop News + ARES: success).
- Quatro notas editoriais com status verificável, links de referência e data; histórico inclui consultas a `main`, `feature/protocolo-ruby-v0.1` e `exp-008-reduced-feistel`.
- Validação no ambiente publicado: homepage renderiza quatro cards; API contém quatro destaques e 12 registros de atividade; interface exibiu commits identificados com `PROTOCOLO RUBY` e `OUROBOROS EXP-008`.
- No instante da validação, as fontes externas estavam parcialmente disponíveis (Hacker News e GitHub entre as quatro fontes principais); a indisponibilidade é indicada na interface. Não inferir que todo site externo esteja inativo permanentemente.
- **Importante:** notas editoriais são revisadas manualmente para cada publicação; apenas feeds e commits seguem atualização automática conforme cache. Alterações posteriores da branch não estão automaticamente publicadas no Pages.


### Correção de conectividade GitHub — 30/10/2026

- **Problema identificado:** respostas intermitentes das consultas à API pública do GitHub no ambiente Cloudflare; isso podia ocultar os commits e confundir o status do GitHub com o feed independente `github.blog`.
- **Solução:** indicadores independentes para API do repositório, GitHub Blog, Cloudflare Blog e Hacker News. O agregador tenta primeiro GitHub REST e, se falhar, o feed Atom público de commits em `github.com`.
- **Contingência final:** quando ambos os caminhos falham, três referências verificadas em 30/10/2026 são exibidas com marcação explícita `REFERÊNCIA VERIFICADA`, sem reivindicar atualização em tempo real.
- **Deploy:** `aae8ce82-6598-42c7-9932-7a27154b6966`, Cloudflare Pages production success, origem `e2a1d559d0d9a5eece95520761c2307e65ed7402`.
- **Validação publicada:** `/api/feed` respondeu com `githubMode: atom`, `githubCommits: true`, duas branches e 12 registros de atividade. A homepage exibiu `GITHUB CONECTADO`, a indicação de feed alternativo e os cards de commits.
- Fontes de notícias externas podem variar entre solicitações/PoPs. A presença de `FONTES PARCIAIS` **não** significa indisponibilidade do repositório.
- Segurança preservada: URLs fixas de GitHub, TLS obrigatório, redirecionamento limitado ao próprio host e parser Atom com links HTTPS restritos a `github.com`.
- Publicação continua por Direct Upload manual; GitHub PR #11 segue em revisão.


## Cronograma público NOV–DEZ 2026

- Página: https://workshop-news.pages.dev/#cronograma
- Documento de planejamento versionado: [Workshop roadmap 2026](../../docs/roadmaps/workshop-2026-nov-dec.md).
- Oito janelas semanais de 02/11 a 27/12, com estados iniciais PLANEJADO e critérios de conclusão por projeto.
- O cronograma é HTML estático no homepage para permanecer legível mesmo que o GitHub e outras fontes estejam indisponíveis.
- Atualizações dos estados exigem revisão humana e evidência de conclusão. O portal não considera planejamento um lançamento.


### Release do cronograma público — 30/10/2026

- **Cloudflare Pages produção:** https://workshop-news.pages.dev/#cronograma
- **Deploy ID:** `823b8f62-429c-480f-9b8b-07f7c6644dec` — status `success`.
- **Código publicado:** `91775959fc526dba4fec57a27c1d61eda8740aa0`, branch `feat/workshop-news-portal-20261030`.
- **Conteúdo:** oito semanas planejadas entre 02/11 e 27/12/2026, com marcos, critérios e links para os projetos.
- **Verificação em produção:** homepage contém link `#cronograma`, oito cards, datas e conteúdo esperado; as suítes GitHub Actions Workshop News e ARES finalizaram com sucesso.
- **Observação:** seção HTML estática, disponível sem feed de notícias; as datas são propostas de trabalho, não compromisso de entrega. Alterações da branch só chegam ao Cloudflare em novo Direct Upload.

## Roadmap em destaque: somente projetos principais (v1.1)

A seção `#cronograma` agora prioriza cinco projetos: Protocolo Ruby, ARGUS/HeartAI, Cerberus, Ouroboros EXP-008 e WolfPack OS. Todos os cards têm janela proposta, marco de validação, status inicial PLANEJADO e link ao projeto. O layout usa cartões com acentos distintos e adapta-se a telas pequenas.

**Atenção:** o cronograma operacional anterior de oito semanas, incluindo segurança, manutenção do News e retrospectiva, segue preservado em [docs/roadmaps/workshop-2026-nov-dec.md](../../docs/roadmaps/workshop-2026-nov-dec.md). As etapas de apoio foram removidas apenas da vitrine pública. As datas não representam anúncios de lançamento.


### Publicação do roadmap visual (cinco projetos) — 30/10/2026

- Produção: https://workshop-news.pages.dev/#cronograma
- Cloudflare Pages deployment: `bee69a72-71c2-4249-988a-2f176ef42d71`, status `success`.
- Runtime originado da branch `feat/workshop-news-portal-20261030`, commit `38223fcc49c71e998bfe561b6ad0040334d3fab2`.
- Novo layout: cinco cards coloridos por projeto, links próprios, objetivos, critérios de validação e janela proposta.
- Testes automatizados de segurança e markup aprovados no CI. Navegador Cloudflare confirmou no site público `#cronograma`, os cinco projetos `ruby`, `argus`, `cerberus`, `ouroboros`, `wolfpack`, e a ausência dos antigos cards administrativos.
- O documento de oito semanas continua armazenado como planejamento interno e histórico, sem exclusão de tarefas transversais.
- A publicação é Direct Upload manual. Documentação alterada posteriormente não indica redeploy automático.


### Refinamento visual do calendário — 30/10/2026

- O roadmap público foi refinado para um visual mais editorial: trilho temporal horizontal, cards com profundidade, hierarquia tipográfica mais limpa, acentos discretos por projeto e comportamento responsivo em 5 → 3 → 2 → 1 colunas.
- Conteúdo preservado: Protocolo Ruby, ARGUS/HeartAI, Cerberus, Ouroboros e WolfPack OS, com as mesmas datas, objetivos, critérios e links.
- CI Workshop News: `a839c62521c3b65bcb39456a77d6194a405ed2cf` — **success**.
- Cloudflare Pages produção: deployment `4948b397-6c75-42db-90a0-2649190f91aa` — **success**.
- A API de Browser Rendering atingiu limite temporário de requisições durante a checagem pós-deploy; o deploy e a suíte automatizada confirmaram os arquivos publicados, mas não registrar uma inspeção visual remota como concluída.

### Remoção do cronograma público — 30/10/2026

- A seção `#cronograma` e o link de navegação foram removidos do Workshop News.
- Os estilos e testes específicos do calendário público também foram removidos.
- O documento `docs/roadmaps/workshop-2026-nov-dec.md` permanece no repositório apenas como histórico interno de planejamento; não é exibido no portal.


### Edição 002 — novidades de 30/10/2026

- **Produção:** https://workshop-news.pages.dev/
- **Cloudflare Pages deployment:** `bab62116-e7c7-429c-9ff8-c99449f99de0` — status `success`.
- **Runtime publicado:** `8d98322e762543cad385c888726335e18d8f22ec`.
- Destaques atualizados: ARGUS v0.2 e página pública ampliada; HEART_004 embeddings e playground; CERBERUS 03 durable delivery lab; Wolfpack Academy Android draft; Wolfpack Academy API FastAPI draft; Protocolo Ruby em revisão.
- O painel de atividade passa a consultar também `feat/wolfpack-academy-android-starter` e `feat/wolfpack-academy-api-mvp`, além de Protocolo Ruby e Ouroboros.
- Verificação ao vivo confirmou `ED. 002`, seis cards de destaque e preservação do feed de notícias.
- GitHub Actions para a edição permaneceu em estado `queued` no instante da publicação. GitHub Status indicava Actions operacional; a edição foi verificada em preview Cloudflare e depois em produção. Não registrar esse job como PASS enquanto não houver conclusão.


### Atalho Ruby Tool — 30/10/2026

- **Rota pública:** https://workshop-news.pages.dev/ruby
- **Destino fixo:** https://protocolo-ruby.wolfpackworkshop.workers.dev/
- O atalho abre a ferramenta Protocolo Ruby publicada em Worker próprio; não aponta para a seção Ruby do WolfPack OS.
- GET/HEAD retornam 302. Query strings não alteram o destino e outros métodos continuam 405.
- A navegação e o painel Laboratórios exibem o atalho Ruby Tool.

### Correção do destino Ruby Tool — 30/10/2026

- O redirect `/ruby` foi corrigido para `https://protocolo-ruby.wolfpackworkshop.workers.dev/`.
- O destino anterior no WolfPack OS foi substituído para evitar ambiguidade entre o playground embutido e a tool independente.

### Publicação da correção Ruby Tool — 30/10/2026

- **Rota:** https://workshop-news.pages.dev/ruby
- **Destino confirmado:** https://protocolo-ruby.wolfpackworkshop.workers.dev/
- **Cloudflare Pages production deployment:** `a95d7ef3-f5ec-4d89-921d-41db197b864b` — status `success`.
- **Runtime:** `0910565b3a51f3ac63cb79f38bde81dd6866d920`.
- CI Workshop News `41105648667`: **success**.
- Browser Rendering confirmou o destino final com título **Protocolo Ruby · Malware Lab**.
- O teste do redirect mantém destino fixo, query ignorada e 405 para métodos não suportados.

### Edição 003 — EXP-009 e atualização geral — 30/10/2026

- **Produção:** https://workshop-news.pages.dev/
- **Cloudflare Pages deployment:** `5ae91d9e-80a2-4b12-9da7-1b51f7970370` — status `success`.
- **Runtime publicado:** `4d53c1a3d27ef16b872a2c871e941c8c1d0711cb`.
- **CI Workshop News:** run `41112349462` — **success**.
- A edição 003 destaca Ouroboros EXP-009, Protocolo Ruby, ARGUS v0.2, HEART_004, CERBERUS 03 e Wolfpack Academy.
- O feed de atividade agora acompanha também `exp-009-round-function-analysis`.
- EXP-009 é descrito como análise exaustiva da função de rodada: DDT e LAT completas, diferencial máximo 0,25 e correlação absoluta máxima 0,5. O portal não apresenta isso como ataque completo à cifra.
- Verificação ao vivo confirmou `ED. 003`, seis cards, EXP-009 e o atalho correto do Protocolo Ruby.
