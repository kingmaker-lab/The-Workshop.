# 🐺 WOLFPACK — THE WORKSHOP WEB

**Kingmaker · MVP web v0.1 · Ruby Protocol integrado ao navegador**

Site estático da WolfPack com catálogo de aplicações do The Workshop e **Ruby Protocol** (12 missões, quatro atos, editor, dicas, testes de saída, XP, patentes e progresso local).

> A Matilha não aprende Ruby decorando comandos. Aprende escrevendo o código que abre o próximo portão.

## Executar agora

É um site estático: **não precisa de Node, framework ou banco de dados para a primeira versão.**

```bash
cd wolfpack-workshop-web
python3 -m http.server 8000
```

Abra `http://localhost:8000` no navegador. Não abra `index.html` por `file://`: o navegador bloqueia o carregamento normal do `data/lessons.json` e/ou dos módulos de JavaScript nessa modalidade.

**Para rodar Ruby no site**, você precisa de um navegador atual com WebAssembly e uma conexão com a internet na primeira execução. O site usa os pacotes `@ruby/wasm-wasi` e `@ruby/3.3-wasm-wasi`, ambos fixados na versão `2.10.1`, baixados via jsDelivr. O tamanho do interpretador torna a primeira carga mais lenta. O restante da interface, incluindo catálogo, lições, editor e progresso, funciona sem motor remoto. Se a sua rede bloquear o CDN, a execução vai mostrar um aviso, sem simular que o desafio foi aprovado.

**O modo CLI funciona independentemente:** baixe `downloads/wolfpack-ruby-protocol-v0.1.zip`, extraia e execute `ruby play.rb`. Para o CLI, é necessário Ruby 3.x instalado.

## O que funciona neste MVP

- Homepage responsiva com identidade visual WolfPack/Kingmaker.
- **Arsenal da Matilha:** Ruby Protocol jogável e cards de ARES, ARGUS, RAVEN, CERBERUS, HTTP Auditor e Crypto Lab. Os demais cards **são planos de integração**, não aplicações já disponíveis na web.
- Campanha com as **12 lições originais** exportadas de `source/lessons.rb` para `data/lessons.json`.
- Editor Ruby e atalhos `Tab` (dois espaços) e `Ctrl+Enter` (executar/reexecutar).
- Verificação de técnicas ensinadas nas lições + comparação da saída gerada por Ruby para **todos os casos de teste** de cada missão.
- Dicas, exemplos, soluções sob confirmação e erros de sintaxe/execução apresentados no terminal.
- Um Worker dedicado à execução de Ruby WebAssembly: o navegador pode interrompê-lo ao exceder o prazo sem congelar a página.
- Progresso salvo em `localStorage`: codinome, código digitado, XP e missões concluídas. Sem login e sem nuvem nesta versão.
- ZIP da versão CLI original disponível dentro do site.

## Como executar missões

1. Clique em **Iniciar Protocolo**.
2. Leia a teoria, o exemplo e a tarefa.
3. Escreva o código no editor, sem digitar `FIM` (na web o botão executa diretamente).
4. Clique em **Executar código**, escolha seu codinome na primeira vez e clique novamente.
5. Se todos os casos passarem, ganhe 100 XP e avance para a próxima missão.

**Observação:** ao concluir uma missão, o botão passa a avançar para a seguinte; use `Ctrl+Enter` para reexecutar uma missão já concluída.

## Arquitetura

```text
wolfpack-workshop-web/
├── index.html
├── assets/styles.css
├── js/app.js                # UI, níveis, progresso, interação
├── js/ruby-worker.js        # Interpretador Ruby WebAssembly + avaliação
├── data/lessons.json        # Dados exportados do jogo Ruby
├── source/lessons.rb        # Lições originais (fonte canônica)
├── export_lessons.rb        # Recria o JSON a partir das lições Ruby
├── downloads/...zip         # Versão CLI
├── docs/ARCHITECTURE.md
└── tests/test_export.py
```

Para atualizar missões mantendo o jogo original como referência, edite `source/lessons.rb` e execute:

```bash
ruby export_lessons.rb
```

O `source/lessons.rb` foi copiado da versão CLI v0.1. Alterações feitas no site não atualizam automaticamente o arquivo `.zip` do CLI; sincronize os dois antes de publicar novas missões.

## Segurança — leia antes de publicar

**NÃO trate WebAssembly + Web Worker como sandbox segura contra código malicioso.** O Worker ajuda na responsividade e nos prazos de execução, mas não garante limites rígidos de memória nem isolamento de acesso a APIs do navegador. A biblioteca Ruby/WASM possui ponte de interoperabilidade com JavaScript. Para uso na internet, o conteúdo deve ser autoral e supervisionado nesta fase; nunca prometa execução segura de código de terceiros nesta versão.

Antes de abrir a plataforma para usuários desconhecidos, isole a execução em origem separada sem credenciais e estabeleça controles de acesso, CSP rigorosa, limites de recursos verificáveis, auditoria de dependências e revisão de ameaças. Para uma versão multiusuário com backend, execute programas apenas em máquinas/containers efêmeros, isolados, com rede desabilitada e recursos limitados; não faça `subprocess.run()` diretamente no servidor público. Veja `docs/ARCHITECTURE.md`.

O site atual **não envia seu código a um servidor da WolfPack**; ele roda no motor Ruby carregado no navegador e salva os dados no dispositivo do jogador. Os downloads de dependências de terceiros ainda seguem a política normal de requisições de rede do navegador.

## Publicar como site estático

### GitHub Pages

Crie um repositório, coloque o conteúdo da pasta `wolfpack-workshop-web` na raiz, abra **Settings → Pages** e selecione a publicação pela branch principal. Aguarde o link da publicação.

### Netlify / Cloudflare Pages

Crie um projeto estático e publique a pasta `wolfpack-workshop-web` como diretório de saída. **Não há comando de build.** Confirme se o host permite carregar o interpretador WebAssembly a partir de `cdn.jsdelivr.net`.

**Ainda não há contas, ranking global, API nem domínio configurado.** O site é um MVP pronto para testar localmente e preparar publicação, não uma produção multiusuário auditada.

## Validar conteúdo

```bash
python3 -m unittest discover -s tests -v
ruby ../wolfpack-ruby-protocol/test/test_wolfpack.rb  # opcional: se o jogo original estiver ao lado
```

## Próximas versões

v0.2: seleção de perfis, conquistas, melhor acessibilidade no editor, revisão de isolamento, cache versionado do Ruby/WASM; v0.3: autenticação, banco de dados, catálogo editável e integração das ferramentas; v1.0: academia da matilha com trilhas ARES, ARGUS, RAVEN e CERBERUS.

**The Workshop ensina a ferramenta. A WolfPack ensina a pensar com ela.**
