# Workshop Kids 🧩

Divisão infantil da The Workshop. Portal gratuito, sem cadastro, sem publicidade e com atividades adequadas à idade.

## Escopo da versão 0.1
- Landing page responsiva, acessível, com áreas Kids Play, Kids Code, Kids Lab e Kids Create.
- Missão interativa “Detetive de Padrões” com quatro desafios. Execução local no navegador, sem persistência de respostas.
- Área para responsáveis e educadores.
- Sem dependências, cookies da aplicação, analytics de terceiros, chamadas de API, chat, upload ou conta infantil.

## Jogo de programação: Heart e a Missão dos Algoritmos (v0.2)
- Nova rota `/jogar/`, acessível diretamente na página inicial.
- Cinco fases com tabuleiro 5×5, comandos de movimento, algoritmo ordenado, animação por etapas, dicas, desfazer, limpar e repetição `N vezes`.
- Conteúdo sobre sequência, decomposição, planejamento, depuração e laços.
- Sem perfis, comentários, telemetria da aplicação, cookies, persistência ou chamadas de rede pelo jogo.
- Testes: `node --test web/workshop-kids/tests/*.test.mjs`.

## Mascotes oficiais (2/11/2026)
- **Heart**: guia infantil, presente na página inicial, no jogo /jogar/ e no chat /heart/.
- **Blade**: guardião da oficina, apresentado na página inicial.
- Artes originais fornecidas para este lançamento; versões WebP otimizadas em `assets/heart.webp` e `assets/blade.webp` (640 × 640).
- Servidas nas rotas `/assets/heart.webp` e `/assets/blade.webp` pelo próprio Worker, sem carregamento externo pelo navegador.
- Política de conteúdo `img-src 'self'` e testes automatizados com `node --test web/workshop-kids/tests/*.test.mjs`.

## Deploy
Código fonte: `web/workshop-kids/worker.js`. Implantado como Worker independente `workshop-kids` no Cloudflare. URL prevista: `https://workshop-kids.wolfpackworkshop.workers.dev/`.

Deploy manual: `npx wrangler deploy web/workshop-kids/worker.js --name workshop-kids --compatibility-date 2026-11-02`

## Segurança e privacidade
- Somente GET e HEAD; rotas explícitas: `/`, `/index.html`, `/styles.css`, `/app.js`, `/jogar/`, `/jogar/index.html`, `/game.css`, `/game.js`.
- CSP restritiva: scripts/estilos próprios e sem saída de rede pelo cliente.
- Cabeçalhos HTTP de segurança e ausência de scripts terceiros.
- Não coleta dados pessoais via funcionalidade do jogo. Logs de infraestrutura do provedor são distintos e devem ser avaliados na política pública de privacidade.
- Antes de funcionalidades com contas, interação social, telemetria ou novos conteúdos físicos, realizar revisão de acessibilidade, proteção infantil e LGPD.

## Próximas etapas
1. Testes automatizados de interface e acessibilidade.
2. Conteúdos revisados por faixa etária e orientação de educadores.
3. Política de privacidade e mecanismos para responsáveis antes de ampliar a plataforma.
4. Integração editorial no portal da The Workshop após validação.

## Heart Core 0.3: chatbot educativo integrado
- Rota `/heart/` e assets `/heart.js`, `/heart.css`, diretamente no mesmo Worker do portal.
- API `POST /api/heart`, apenas mesma origem, JSON limitado a 1024 bytes e mensagens de até 220 caracteres.
- Faixa Exploradores (4–6) recebe respostas guiadas; para Inventores/Criadores, assuntos escolares previamente delimitados podem usar Workers AI (Llama 3.2 3B) com Llama Guard na entrada e na saída. Se AI indisponível, resposta guiada.
- Nenhum dado de conversa é guardado em banco/localStorage; rate limit temporário na memória da instância do Worker (não é rate limit global). O provedor pode tratar logs operacionais e textos enviados para inferência. Não existem autenticação infantil, chat entre usuários ou ferramentas executáveis.
- Os filtros são incompletos e não garantem segurança. Revisão de salvaguardas, carga, acessibilidade e LGPD/ECA Digital antes de expandir chat. Limites globais Cloudflare devem ser configurados no painel.
- Deploy exige Workers AI binding `AI` (`{type:"ai",name:"AI"}`). O modelo utiliza a franquia e pode gerar custos conforme o plano da conta.


## Base Blade 🛡️ (segurança digital infantil)
- Nova rota `/blade/`, dedicada ao personagem Blade e a educação de autoproteção digital.
- Missões guiadas de senhas, mensagens suspeitas, privacidade, respeito e aplicativos.
- Conversa usando `/api/blade` com conteúdo preparado por padrão; IA opcional nas trilhas 7–12 com seleção de responsável, controles de segurança e sem histórico persistente no aplicativo.
- Informações e limitações detalhadas no arquivo `web/workshop-kids/BLADE.md`.
