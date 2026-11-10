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

## Publicação independente com Cloudflare Workers

A Store usa o módulo estático de `web/workshop-store/` e um Worker separado dos demais portais, com build reproduzível.

```sh
node web/workshop-store/build.mjs
node --check web/workshop-store/dist/worker.mjs
npx wrangler deploy --config web/workshop-store/wrangler.toml
```

Preview disponibilizado via Cloudflare Workers no endereço:
https://workshop-store-preview.wolfpackworkshop.workers.dev/

O preview usa um Worker independente chamado `workshop-store-preview`; a configuração e o código estão no mesmo branch deste PR. Nenhum site existente foi substituído.

O contato WhatsApp comercial está configurado em `config.js`. **O preview não significa aprovação comercial dos preços nem lançamento definitivo.** Revise serviços e preços iniciais antes de publicar `workshop-store` em produção e adicionar o link aos hubs existentes.

Os valores são estimativas “a partir de” e o cliente negocia o escopo do serviço no WhatsApp.

## Limites

- Não recebe pagamentos, não faz agendamentos e não mantém pedidos.
- Sem painel administrativo: catálogo e contato são versionados.
- Preços sugeridos precisam de validação antes do lançamento.
- Visitas presenciais dependem de localização, orçamento e disponibilidade.
- Avaliações de segurança apenas em ambientes com autorização formal.
