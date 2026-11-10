# The Workshop Store — MVP v0.1

Vitrine comercial independente para **assistência técnica, automação, sites/sistemas e segurança digital**. Complementa os Labs gratuitos sem os modificar.

## Funcionalidades
- Catálogo com 16 ofertas em quatro áreas, busca e filtros.
- Preços a partir de valores de referência; preço final após avaliação e aceite de orçamento.
- Seleção múltipla, cálculo separado de valores pontuais e mensais.
- Link por produto e botão para enviar lista completa como texto ao WhatsApp.
- HTML, CSS e JS estáticos, sem backend, rastreamento, banco de dados, checkout ou cobrança.
- Layout responsivo, navegação por teclado e cabeçalhos de segurança.

## Obrigatório antes do lançamento: número comercial

Configure um **WhatsApp autorizado para uso público** no arquivo config.js:

    window.WORKSHOP_STORE = Object.freeze({
      whatsapp: "55DDDNUMERO"
    });

Troque pelo número real, iniciando com 55 + DDD + telefone, somente dígitos. O valor ilustrativo acima não é válido. Com o valor vazio, todos os botões de WhatsApp ficam desativados e há uma mensagem explicativa. **Não publique antes de configurar o contato verdadeiro.** O telefone ficará público no código da página, pois o link WhatsApp é público.

Ao clicar, o visitante abre o próprio WhatsApp com mensagem pré-preenchida. A loja não mantém os dados da conversa nem envia informações a um servidor Workshop.

## Preços e ofertas
Edite catalog.mjs. O atributo price informa referência em reais e period: "mês" identifica opção mensal, sem cobrança automática. Defina limites claros para suporte e manutenção antes de aceitar contratos. Serviços de segurança exigem autorização expressa e escopo escrito.

## Testes

    node --check web/workshop-store/app.js
    node --check web/workshop-store/config.js
    node --test web/workshop-store/tests/*.test.mjs

## Publicação isolada no Cloudflare Pages

Módulo estático independente, seguindo o padrão de Direct Upload dos portais atuais. Faça deploy **após configurar o contato e revisar o catálogo**:

    npx wrangler pages project create workshop-store --production-branch main
    npx wrangler pages deploy web/workshop-store --project-name workshop-store --branch main

Se o projeto já existir, pule o comando de criação. Confirme que os arquivos foram servidos, teste no celular e verifique o envio da mensagem. Adicionar um link a partir dos hubs existentes deve ser uma alteração posterior e separada, preservando Labs, CTF e Kids.

## Limites
- Não recebe pagamentos, não faz agendamentos e não mantém pedidos.
- Sem painel administrativo: catálogo e contato são versionados.
- Preços são sugestões iniciais, não promessa de preço final.
- Visitas presenciais dependem de localização, orçamento e disponibilidade.
- Avaliações de segurança apenas em ambientes com autorização formal.
