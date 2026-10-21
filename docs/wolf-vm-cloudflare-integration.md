# WOLF-VM — Plano de integração com o ecossistema Cloudflare

**Status atual: OFFLINE — deploy expressamente suspenso.**
**Data:** 2026-10-21  
**Versão técnica:** v0.1 (código publicado em `wolf-vm/`, porém sem publicação da interface em Cloudflare).

## Objetivo

O WOLF-VM deve ser divulgado como um **módulo do The Workshop**, conectado aos demais laboratórios do ecossistema Cloudflare e ao registro do Cerberus, e não como uma página pública isolada.

## Pontos de integração a preparar antes da publicação

| Plataforma | Endereço | Integração planejada |
| --- | --- | --- |
| Workshop Labs (portal central) | https://workshop-labs.pages.dev/ | Card do WOLF-VM, página técnica própria, navegação de volta ao hub e links ao código. |
| WolfPack OS (hub) | https://wolfpack.wolfpackworkshop.workers.dev/ | Card/entrada do WOLF-VM apontando para a rota final do Workshop Labs. |
| Cerberus (arquitetura) | https://cerberus.wolfpackworkshop.workers.dev/ | Inventário/registro central, status, versão e URL do laboratório; nenhuma ativação automática enquanto offline. |
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

**OFFLINE / NÃO PUBLICAR AINDA.** Retomar apenas com uma implantação coordenada dos demais sites.
