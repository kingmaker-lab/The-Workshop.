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

## Blade 2.0: guardião digital (02/11/2026)
- Nova arte fornecida pelo projeto, otimizada como `web/workshop-kids/assets/blade.webp` (768 × 768).
- Imagem substituída na vitrine dos mascotes e exibida integralmente na seção `/#blade`, com destaque para privacidade, direitos, proteção e navegação consciente.
- A seção direciona famílias e educadores ao aviso `/#responsaveis`; o aviso mantém o acesso a `https://workshop-news.pages.dev/#workshop`.
- A rota pública `/assets/blade.webp` mantém-se interna ao Worker, sem chamada a fornecedores de imagens.
- O binding `AI` do Heart foi preservado no deploy.

## Blade v3: página própria com quadrinho educativo
- Nova arte fornecida pelo projeto e otimizada para `assets/blade.webp` (960 × 960), incorporada ao Worker sem rede de terceiros.
- Acesso em `/blade/` (`/blade`, `/blade/index.html`) com CSS dedicado `/blade.css`; sem JavaScript de cliente.
- Apresentação do personagem, três princípios (proteger, questionar, pedir ajuda) e quadrinho de quatro cenas: "O clique misterioso", sobre mensagens suspeitas, privacidade e adulto de confiança.
- Link permanente no menu, no card do mascote e na seção `/#blade` da página inicial. Links de retorno para a Heart e o jogo.
- Chamada para responsáveis aponta para `https://workshop-news.pages.dev/#workshop`.
- Nova página com `script-src 'none'`, `connect-src 'none'`, assets somente da própria origem; sem formulário ou coleta de dados.
- Executar `node --test web/workshop-kids/tests/*.test.mjs` antes de publicar novas mudanças.


## Blade: espaço de perguntas sobre segurança infantil
- Mantida a página `/blade/` e o quadrinho de quatro cenas sem JavaScript.
- Nova rota `/blade/conversar/` com respostas guiadas e IA moderada, opcional para 7–12 anos com participação do responsável.
- Conteúdos: golpes, senhas, privacidade e cidadania digital. Documentação: `web/workshop-kids/BLADE-CHAT.md`.

## Próximo mascote: teaser e interação futura (02/11/2026)
- A página inicial ganhou a seção `/#novidades-mascotes` com Blade, Heart e a silhueta preta de um mascote misterioso (`?`).
- Card responsivo usando somente `/assets/blade.webp`, `/assets/heart.webp` e CSS interno, sem dependências nem chamadas a serviços de imagens.
- Mensagem editorial: futuramente todos os mascotes da The Workshop poderão interagir com visitantes nas plataformas do ecossistema. O novo mascote ainda está em preparação.
- Os links de conversa que já existem são `/heart/` e `/blade/conversar/`; interações com crianças mantêm orientações de privacidade, supervisão de responsáveis e revisão de segurança antes de expansão.

## Heart e Blade: chats separados, apresentação v4 (02/11/2026)
- O portal passa a oferecer **dois cards de conversa** em `/#conversar`, um para cada mascote.
- **Heart:** `/heart/`, chat independente `/api/heart`, visual claro, roxo/rosa e assuntos de ciência, programação e descobertas.
- **Blade:** `/blade/conversar/`, chat independente `/api/blade`, visual preto/vermelho, acesso direto à arte atual `/assets/blade.webp?v=e04bfb99` e conteúdos educativos de segurança digital.
- Ambos possuem navegação cruzada com seleção explícita do chat ativo, trilhas por faixa etária e avisos aos responsáveis.
- A arte do Blade recebe um parâmetro de versão para evitar o cache da imagem anterior. O backend de IA, os controles de privacidade e os filtros preexistentes não foram alterados.
- Política infantil: sem chat entre usuários, sem armazenamento de histórico no site, perguntas limitadas, orientação a não fornecer informações pessoais e IA opcional para maiores faixas supervisionadas. Limites do provedor permanecem aplicáveis.
- Smoke tests e testes de interface via `node --test web/workshop-kids/tests/*.test.mjs` e `.github/workflows/workshop-kids-live.yml`.
