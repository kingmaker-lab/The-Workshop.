# WolfPack OS v0.4.1 — atualização segura de cards

## Escopo
Somente os cards ARES e CERBERUS na página inicial. **Nenhum jogo, asset ou download deve ser substituído.**

- ARES: https://workshop-labs.pages.dev/projects/ares/
- CERBERUS: https://cerberus.wolfpackworkshop.workers.dev/ — **Arquitetura de Software**, não orquestração.

## Técnica de deploy
A versão pública v0.4.0 do Worker `wolfpack` é asset-only (static assets); o código do site v0.3 no GitHub está defasado. Em vez de substituir sua distribuição estática, `worker.js` aplica um HTMLRewriter **somente à página inicial** através de `env.ASSETS`.

Usar a API Workers com metadados:
```json
{
  "main_module": "wolfpack.js",
  "compatibility_date": "2026-10-19",
  "keep_assets": true,
  "assets": {
    "config": {
      "html_handling": "auto-trailing-slash",
      "not_found_handling": "none",
      "run_worker_first": ["/", "/index.html"]
    }
  },
  "bindings": [{"name": "ASSETS", "type": "assets"}]
}
```
`keep_assets` preserva o manifesto já publicado no Cloudflare; `run_worker_first` permite interceptar somente `/` e `/index.html`; outras URLs continuam static-first. O handler também encaminha caminhos que não sejam a home para `env.ASSETS.fetch`, caso uma mudança de regras amplie a interceptação.

## Segurança
- Destinos fixos, sem query parameters dinâmicos, open redirect, iframe ou novas dependências de terceiros.
- Sem scripts adicionais no cliente, sem CORS, cookies, storage ou novas permissões.
- `rel="noopener noreferrer"`, `referrerpolicy="no-referrer"`, foco acessível.
- Não modificar JS do Ruby Protocol, VULPES-77 ou RAVEN, nem ZIPs.
- Remove ETag, Last-Modified e Content-Length no HTML transformado para evitar metadados incorretos.
- Manter versão anterior do Worker disponível para rollback.
- Verificar as rotas: `/`, `/js/ruby-worker.js` e três URLs de download.

## Verificação
`node --test web/wolfpack-os-v04-linker/worker.test.mjs`.

**Limite**: testes unitários não equivalem a auditoria do browser ou do deploy; após publicar, testar todas as experiências diretamente no site.
