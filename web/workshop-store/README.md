# The Workshop Store — MVP v0.1

Vitrine comercial independente para **assistência técnica, automação, sites/sistemas e segurança digital**. Complementa os Labs gratuitos sem os modificar.

## Funcionalidades
- Catálogo com 16 ofertas em quatro áreas, busca e filtros.
- Preços a partir de valores de referência; preço final após avaliação e aceite de orçamento.
- Seleção múltipla, cálculo separado de valores pontuais e mensais.
- Link por produto e botão para enviar lista completa como texto ao WhatsApp.
- HTML, CSS e JS estáticos, sem backend, rastreamento, banco de dados, checkout ou cobrança.
- Layout responsivo, navegação por teclado e cabeçalhos de segurança.

## WhatsApp comercial

O contato autorizado foi configurado em `config.js` e todos os botões usam a rota fixa `https://wa.me/` com telefone brasileiro validado. O número é **informação pública** de atendimento e não deve ser considerado segredo. Se houver troca de telefone, faça revisão e teste de regressão; mantenha o contato em arquivo de configuração, nunca em diversos componentes.

A mensagem é apenas pré-preenchida: **o visitante precisa confirmar o envio no WhatsApp**. A Store não armazena a conversa.

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

## Gate de segurança\n\nA revisão e os bloqueadores de produção estão documentados em [SECURITY_RELEASE_REVIEW_2026-11-10.md](SECURITY_RELEASE_REVIEW_2026-11-10.md). Antes de publicar, seguir também o documento raiz [SECURITY_RELEASE_GATE.md](../../docs/SECURITY_RELEASE_GATE.md).\n\n## Limites

- Não recebe pagamentos, não faz agendamentos e não mantém pedidos.
- Sem painel administrativo: catálogo e contato são versionados.
- Preços sugeridos precisam de validação antes do lançamento.
- Visitas presenciais dependem de localização, orçamento e disponibilidade.
- Avaliações de segurança apenas em ambientes com autorização formal.
