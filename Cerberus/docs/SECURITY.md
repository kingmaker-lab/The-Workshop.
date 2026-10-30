# Security Review — CERBERUS v0.4 / 2026-10-30

## Escopo

Este documento cobre somente o laboratório público de arquitetura de software. Ele não garante a segurança do Ares, Crypto Lab ou WolfPack OS e não declara que os futuros experimentos de arquitetura estejam em produção.

## Modelo de ameaças

**Ativos:** integridade da documentação, disponibilidade do Worker, privacidade de visitantes, reputação dos links e integridade do repositório.

**Ameaças:** modificação indevida de conteúdo, XSS, clickjacking, open redirect, mistura de origem/credenciais, supply chain de frontend, exposição involuntária de rotas e regressões de deploy.

## Controles do Worker

- GET/HEAD somente, demais métodos 405 e rotas desconhecidas 404.
- Sem scripts de cliente, bibliotecas externas, backend de escrita, formulários ou credenciais.
- Links externos declarados em código, usando HTTPS, `rel="noopener noreferrer"` e `referrerpolicy="no-referrer"`.
- CSP restritiva com `script-src 'none'`, `connect-src 'none'`, `frame-ancestors 'none'`, `form-action 'none'`, `object-src 'none'` e `base-uri 'none'`.
- Exceção documentada: CSS embutido exige `style-src 'unsafe-inline'`, sem permissão de JavaScript embutido.
- `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Permissions-Policy`, HSTS.
- Não usa cookies, segredo, token, KV, D1, R2 ou service bindings.

## Gate de mudança

1. Verificar escopo da alteração e impacto no site ativo.
2. `cd Cerberus && npm test` (Node 20+).
3. Conferir página inicial, experimentos 01/02/03, `/api/status`, `/api/modules` e `/api/projects`.
4. Inspecionar cabeçalhos efetivamente recebidos e links externos em deploy de preview/produção.
5. Validar responsividade, navegação por teclado e funcionamento de recursos preservados.
6. Confirmar rollback para versão anterior no dashboard.

## Limites

Testes de unidade não verificam TLS, DNS, WAF, funcionalidades de outros Workers nem métricas reais de performance. Revisões de segurança são contínuas, não uma garantia absoluta.

## Bancada 03: modelo de ameaça da simulação local

- O endpoint de testes liga exclusivamente a `127.0.0.1` em porta efêmera e rejeita métodos/rotas inesperados.
- Corpo JSON de no máximo 4096 bytes, verificação de Content-Type e esquema estrito de campos com IDs limitados.
- Outbox e reserva são transacionadas com comandos SQL parametrizados; consumidor recusa payload conflitante para mesmo ID (HTTP 409).
- Dispatcher aceita exclusivamente URL HTTP com hostname `127.0.0.1` e porta explícita; não é um proxy genérico.
- Não há autenticação, anti-CSRF, TLS, rate limit, proteção multiusuário, isolamento forte, agendamento de retentativas nem broker. **Não implantar o receptor local na Internet.**
- `script-src 'none'` no Worker continua intacto: página 03 utiliza componentes HTML nativos (`details`) para mostrar os passos, sem executar JavaScript do cliente.
