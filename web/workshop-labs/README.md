# Workshop Labs — Hub versionado do CERBERUS

Código-fonte do **candidato** ao portal estático de navegação do Workshop, com card do WolfPack OS. O Pages atual foi implantado diretamente no Cloudflare, sem fonte Git associada; por isso esta implementação está isolada em branch para revisão e publicação controlada.

- Worker: `_worker.js`, sem dependências.
- Testes: `node --test tests/smoke.test.mjs` com Node.js 20+.
- Rotas: `/`, `/index.html`; outras rotas 404.
- Segurança: headers CSP, XFO, nosniff, HSTS, Permissions-Policy e Referrer-Policy.
- Deploy via Wrangler: `npx wrangler pages deploy web/workshop-labs --project-name workshop-labs --branch cerberus-preview` (verifique permissões e políticas da conta). **Não execute produção sem validar preview e garantir backup/rollback.**
- Fonte: `Cerberus/registry/projects.json` documenta os destinos e seus estados. Na fase 1, os links também estão embutidos no HTML, reduzindo requests e dependências; um gate deve checar consistência entre ambos.
