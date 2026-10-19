# WolfPack OS v0.4.1 — atualização segura de cards

## Escopo
Somente os cards ARES e CERBERUS na página inicial. **Nenhum jogo, asset ou download deve ser substituído.**

- ARES: https://workshop-labs.pages.dev/projects/ares/
- CERBERUS: https://cerberus.wolfpackworkshop.workers.dev/ — **Arquitetura de Software**, não orquestração.

## ⚠ Resultado do teste de publicação (19/10/2026)

A API Cloudflare aceitou a criação de uma nova versão com `keep_assets:true`, e o código foi preservado, porém a configuração efetiva retornou **`serve_directly:true` e `raw_run_worker_first:false`**, apesar de solicitar `run_worker_first`. Portanto, o arquivo estático continua respondendo antes que o `HTMLRewriter` seja executado, e **os cards não foram publicados no domínio principal**.

A versão experimental foi implantada somente para validar esse comportamento, e a implantação original foi restaurada (Worker versão `53fcb16b-5a66-432f-abeb-1611cd4866b1` a 100%). Nenhum asset foi apagado.

**Não republicar somente este Worker como se fosse correção completa.** Para tornar a alteração efetiva, precisamos do diretório completo da build estática v0.4.0 (HTML, `/js/ruby-worker.js` e `/downloads/*.zip`) e publicar um novo manifesto de assets com o HTML corrigido, preservando os demais arquivos e os controles de segurança. Um HTML salvo pelo navegador, sem o conjunto de assets, não substitui essa build.

## Técnica de deploy (proposta, ainda bloqueada)
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

## Estado final

- Código do linker e testes versionados, mas **não utilizado em produção**.
- Correção do HTML feita a partir do snapshot v0.4.0 recebido do usuário (arquivo de exportação entregue no chat), com os cinco scripts inline preservados byte a byte.
- A futura publicação deve comparar os hashes dos downloads e validar Ruby/VULPES/RAVEN antes de acionar 100% do tráfego.
