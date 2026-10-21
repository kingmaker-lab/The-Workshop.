# CERBERUS_02 — Runbook de deploy seguro

## Situação em 21/10/2026

O experimento e a página estão versionados no GitHub, com testes automáticos aprovados. A publicação na Cloudflare **não deve ser declarada concluída** até que uma implantação seja confirmada e `scripts/live-smoke.mjs` passe no domínio público.

## Publicação oficial

O arquivo `Cerberus/wrangler.toml` usa o mesmo Worker **cerberus** já existente. Nenhum binding de banco, credenciais ou outros Workers é necessário. A plataforma WolfPack e o Workshop Labs não precisam ser modificados.

Com uma sessão Cloudflare autorizada, executar localmente:

```bash
cd Cerberus
node --test worker.test.mjs
# Primeira utilização: npx wrangler@4 login
npx wrangler@4 deploy --config wrangler.toml
node scripts/live-smoke.mjs
```

O comando usa `wrangler@4` (major version); para reprodutibilidade estrita, fixar versão e hash no ambiente de release. **Nunca enviar tokens de API em issues, commits ou chat.**

## Critérios de aceite

- Cloudflare indica a nova versão recebendo 100% do tráfego, com rollback disponível.
- `/` mostra CERBERUS_01 e CERBERUS_02 como disponíveis.
- `/labs/01` continua funcional; `/labs/02` responde 200 e apresenta o estudo.
- `/api/modules` tem `cerberus-02: available`; `/api/status` indica `version: 0.3.0` e `available_labs: 2`; `/api/projects` permanece estável.
- CSP bloqueia JavaScript no portal; frames e sniffing bloqueados; GET/HEAD e 404/405 esperados.
- Execução Python do experimento foi validada no GitHub Actions, não há banco de dados no Worker.

## Reversão

No painel Cloudflare Workers & Pages, selecionar o Worker `cerberus`, abrir **Deployments** e reativar a versão anterior (CERBERUS 0.2.0) caso haja regressão. Não editar no painel sem sincronizar `Cerberus/worker.js` com o GitHub.

## Segurança

O site só serve HTML e JSON públicos; a aplicação de reservas é um laboratório Python local, não um endpoint HTTP produtivo. Não adicionar CORS permissivo, credenciais nem armazenar dados pessoais no Worker.
