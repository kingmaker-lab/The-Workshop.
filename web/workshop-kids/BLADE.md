# Base Blade · segurança digital infantil

Blade é o mascote da The Workshop Kids dedicado a segurança e cidadania digital. A rota `/blade/` fica isolada do chat Heart e dos jogos, mas é servida pelo mesmo Worker, com imagem própria.

**Escopo:** senhas fortes, autenticadores, golpes, phishing, privacidade, imagens, respeito online, cyberbullying, permissões de aplicativos e atualizações. Há um quiz fechado sobre mensagens de prêmios e senhas.

**Faixas etárias:** 4–6 recebe somente respostas preparadas. Faixas 7–9 e 10–12 também começam guiadas; IA generativa é opcional e depende de seleção explícita pelo responsável. A caixa não comprova identidade nem constitui verificação legal de consentimento.

**Segurança:** sem ferramentas, código executável, uploads, perfis, armazenamento de conversas no aplicativo ou contato entre crianças. A API aceita somente JSON de mesma origem, mensagens de até 220 caracteres, corpo máximo de 1024 bytes, e aplica filtros determinísticos na entrada, mais Llama Guard antes/depois da inferência. Respostas podem falhar ou ser imprecisas, portanto a supervisão adulta continua indispensável.

**Privacidade:** este código não armazena mensagens, mas o provedor de infraestrutura/IA pode processar dados operacionais e conteúdo enviado para inferência. O controle de uso atual é apenas temporário por instância, não global. Revisar LGPD, ECA Digital, transparência e limitações globais na Cloudflare antes de expandir.

**Código:** `web/workshop-kids/worker.js`, rotas `/blade/`, `/blade.css`, `/blade.js`, `POST /api/blade`. Testes: `node --test web/workshop-kids/tests/*.test.mjs`.
