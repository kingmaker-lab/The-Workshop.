# CERBERUS — Workshop Integration & Governance

> **Build. Break. Understand. Rebuild.**

Cerberus é o módulo de integração **não privilegiada** do ecossistema The Workshop. Nesta fase, ele é um catálogo declarativo com regras de governança, não um agente com acesso a credenciais, redes internas ou ferramentas administrativas.

## Módulos planejados

| Módulo | Escopo | Fase |
|---|---|---|
| CERBERUS-CORE | registro de aplicações, metadados e versionamento | fase 1 |
| CERBERUS-GATE | links fixos, allowlist de destinos e navegação acessível | fase 1 |
| CERBERUS-SENTRY | verificação de cabeçalhos e regressões pós-deploy | fase 1 (testes) |
| CERBERUS-STATUS | indicadores de saúde com coleta somente autorizada, posteriormente | planejado |
| CERBERUS-ORCHESTRATOR | automação entre módulos, autenticação e permissões explícitas | futuro, fora do escopo |

## Contratos da fase 1

- Portal: `https://workshop-labs.pages.dev/`.
- WolfPack OS: `https://wolfpack.wolfpackworkshop.workers.dev/`.
- Ares: `https://workshop-labs.pages.dev/projects/ares/`.
- Crypto Lab: `https://wolfpack-crypto.pages.dev/`.
- Metadados em `registry/projects.json`, com destinos HTTPS explícitos.
- Links nativos HTML, sem iframe, redirecionador dinâmico, proxy, CORS de integração ou JavaScript remoto.
- O catálogo **não** autentica usuários e **não** transmite estado, progresso, tokens ou dados de laboratório entre origens.
- Cada aplicativo mantém seu próprio ciclo de deploy e fronteira de confiança.

## Diretórios

```text
Cerberus/
├── README.md
├── registry/projects.json
└── docs/SECURITY.md
web/workshop-labs/
├── _worker.js
├── README.md
└── tests/smoke.test.mjs
```

## Roadmap de integração

1. Mostrar WolfPack OS no portal como terceiro laboratório, com link externo seguro.
2. Manter Ares e Crypto Lab funcionando nos URLs anteriores.
3. Formalizar catálogo, cabeçalhos defensivos e smoke tests.
4. No futuro, adicionar indicadores de status, sem executar scans nem coletar dados sem autorização.
5. Só criar orquestração com modelos explícitos de identidade, autorização, auditoria e limites.
