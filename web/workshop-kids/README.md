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
