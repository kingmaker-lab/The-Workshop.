# Blade: chat educativo de segurança infantil

A página principal do Blade continua em `/blade/`, com a arte e o quadrinho de quatro cenas **O clique misterioso**. O espaço de perguntas funciona separadamente em **`/blade/conversar/`** e é acessível por links no portal e na página do quadrinho.

## Conteúdo
- Senhas e códigos de verificação, golpes e phishing, fotos e privacidade, respeito digital e cyberbullying, permissões de aplicativos e atualizações.
- Missão interativa de escolha segura diante de pedido de senha por desconhecido.
- Faixa 4–6: respostas fixas, sem geração.
- Faixas 7–9 e 10–12: respostas fixas por padrão e IA opcional, sob seleção declaratória de um responsável.

## Arquitetura e segurança
- Cloudflare Worker `workshop-kids` no mesmo domínio; rotas `/blade/conversar/`, `/blade/chat.css`, `/blade/chat.js`, `POST /api/blade`.
- Isolamento de HeartAI operacional, sem shell, ferramentas, contas, uploads, perfil, contatos entre crianças ou scripts executáveis na página do quadrinho.
- Entrada com limite de 220 caracteres, 1024 bytes por corpo, JSON same-origin, filtragem de informações pessoais e conteúdo perigoso. Quando habilitada, a IA usa Llama Guard para entrada e saída e responde só a tópicos defensivos.
- Sem persistência de chat no aplicativo. O provedor de infraestrutura/IA pode processar mensagens e dados técnicos; revisar essa informação na política de privacidade.
- Rate limit em memória por instância, **não global**. A caixa de responsável **não é verificação de identidade nem substitui consentimento exigível**.
- Os filtros automáticos são imperfeitos; uma pessoa adulta deve acompanhar. Revisar LGPD, ECA Digital, acessibilidade e limites globais antes de ampliar os recursos.

## Testes
`node --test web/workshop-kids/tests/*.test.mjs`
