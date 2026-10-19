# CERBERUS — Security review / 2026-10-19

## Modelo de ameaça

O portal é público e estático. Seu objetivo é facilitar navegação; jamais receber dados de login, executar comandos, acessar Worker APIs internas, fazer scans no navegador ou transferir dados entre aplicativos.

**Ativos:** integridade do conteúdo, reputação dos links, privacidade dos visitantes, disponibilidade, identidade das origens e isolamento entre projetos.

**Riscos:** link malicioso, XSS em HTML, clickjacking, rastreamento por referrer, dependências de terceiros, regressões após deploy, exposição acidental de recursos administrativos e acoplamento que propague falhas.

## Controles implementados no portal candidato

- URLs HTTPS estáticas; não há parámetro de redirecionamento, `target` arbitrário, iframe, código de terceiros ou `eval`.
- `Content-Security-Policy`: scripts e conexões proibidos, `frame-ancestors 'none'`, formulários e objetos proibidos, `base-uri 'none'`.
- CSS inline autorizado explicitamente em `style-src 'unsafe-inline'`. Isso é uma concessão registrada para manter um documento autocontido; **não** habilitamos inline scripts.
- `Referrer-Policy: no-referrer` e `referrerpolicy=no-referrer` nos links externos.
- `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Permissions-Policy` restritiva, HTTPS e HSTS do subdomínio.
- Somente `GET`/`HEAD`; `POST` retorna 405; caminhos desconhecidos retornam 404.
- Sem storage, cookies, analytics, segredos, CORS permissivo ou chamadas externas no catálogo.
- Respeito a `prefers-reduced-motion`; navegação por teclado e `aria-label` nos elementos de navegação.
- Conteúdo estático, CSS local, JS zero e links diretos para menor latência.

## Limites da avaliação

O teste local verifica apenas a lógica do Worker. Segurança de cada laboratório, TLS efetivo, WAF, regras de DNS, SRI, políticas de build e headers realmente recebidos devem ser verificados em um deploy de preview e novamente após qualquer alteração em produção.

## Gate a cada implantação

1. Confirmar que os destinos no registro pertencem ao projeto.
2. Executar `node --test web/workshop-labs/tests/smoke.test.mjs`.
3. Validar manualmente navegação, teclado, viewport móvel, cabeçalhos, status HTTP, latência e isolamento.
4. Comparar comportamento e headers antes/depois (RAVEN pode auxiliar com snapshots autorizados).
5. Manter possibilidade de rollback no Cloudflare Pages; não promover previews com falha.

**Não declarar 'segurança garantida'**: é defesa em camadas e acompanhamento contínuo.
