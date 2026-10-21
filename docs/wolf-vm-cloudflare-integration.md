# WOLF-VM — Plano de integração com o ecossistema Cloudflare

**Status atual: ONLINE — Workshop Labs em produção após preview e validação externa.**
**Data:** 2026-10-21  
**Versão técnica:** v0.1 (código publicado em `wolf-vm/`, porém sem publicação da interface em Cloudflare).

## Objetivo

O WOLF-VM deve ser divulgado como um **módulo do The Workshop**, conectado aos demais laboratórios do ecossistema Cloudflare e ao registro do Cerberus, e não como uma página pública isolada.

## Pontos de integração a preparar antes da publicação

| Plataforma | Endereço | Integração planejada |
| --- | --- | --- |
| Workshop Labs (portal central) | https://workshop-labs.pages.dev/ | Card do WOLF-VM, página técnica própria, navegação de volta ao hub e links ao código. |
| WolfPack OS (hub) | https://wolfpack.wolfpackworkshop.workers.dev/ | Card/entrada do WOLF-VM apontando para a rota final do Workshop Labs. |
| Cerberus (arquitetura) | https://cerberus.wolfpackworkshop.workers.dev/ | Inventário/registro central, status, versão e URL do laboratório; sem executar bytecode remoto. |
| Crypto Lab | https://wolfpack-crypto.pages.dev/ | Navegação institucional entre laboratórios quando fizer sentido, sem confundir o WOLF-VM com um experimento de criptografia. |

Esses destinos são **alvos planejados**, não confirmação de versão online ou permissão de deploy.

## Fonte de verdade e estados

`Cerberus/registry/projects.json` contém a entrada `id=wolf-vm`.

- `offline` — não anunciar o módulo como disponível; preservar desenvolvimento e documentação no GitHub.
- `staged` — somente preview interno, com URL distinta da produção, após preparação do conjunto de sites.
- `online` — usar apenas depois de todos os links necessários e rotas públicas estarem testados e confirmados.

`release_gate=ecosystem_integration_pending` sinaliza que nenhuma publicação em produção foi autorizada.

## Pré-requisitos de publicação

1. Levantar a versão **realmente implantada** de cada site antes de modificá-lo, incluindo backups e plano de rollback.
2. Definir a URL canônica do WOLF-VM no Workshop Labs e a navegação cruzada com WolfPack OS / Cerberus; Crypto Lab com link contextual, caso aplicável.
3. Revisar todos os cards, registries e cabeçalhos HTTP sem alterar rotas funcionais de ARES, Crypto ou Cerberus.
4. Criar **previews** dos sites impactados sem alterar produção.
5. Rodar testes GET/HEAD/404/405, CSP, XFO, no-sniff, HSTS, acessibilidade básica e política de links externos.
6. Validar em previews que links novos não apontam para páginas inexistentes.
7. Promover versões para produção de forma coordenada, com rollback pronto e verificação HTTP real.
8. Somente após a confirmação pública, atualizar o Cerberus para `online`.

**Importante:** a existência do código-fonte de uma rota no repositório NÃO indica deploy no Cloudflare. A versão atual do Worker do Workshop Labs já contém implementação de interface para WOLF-VM que deverá ficar sem publicação até que as integrações sejam liberadas.

## Limites de segurança

- Publicar somente documentação do interpretador, exemplos estáticos e links ao repositório.
- Não executar bytecode arbitrário enviado por usuários no Cloudflare Workers/Pages.
- Nenhum segredo de Cloudflare pode ser versionado no GitHub; deploys devem usar permissões mínimas e credenciais protegidas.

## Decisão

**ONLINE no Workshop Labs.** O card e a rota pública passaram na validação externa. As integrações de catálogo e navegação entre sites são progressivas; modificações nos Workers independentes WolfPack OS e Cerberus não foram realizadas nesta entrega.

## Publicação verificada — 21/10/2026

- Cloudflare Pages: projeto `workshop-labs`, ambiente `production`.
- Deployment: `38ff3eed-95e5-406d-a73b-83240b5ff5bf` (primeira publicação WOLF-VM).
- GitHub Actions: preview https://github.com/kingmaker-lab/The-Workshop./actions/runs/39648272474 e produção https://github.com/kingmaker-lab/The-Workshop./actions/runs/39648499014 com sucesso.
- A navegação do WOLF-VM e do hub aponta para WolfPack OS e Cerberus. Os Workers desses dois projetos não foram alterados nesta publicação.
- Riscos residuais: revisão de links de entrada de outros sites permanece independente e não bloqueia a disponibilidade da página oficial.
