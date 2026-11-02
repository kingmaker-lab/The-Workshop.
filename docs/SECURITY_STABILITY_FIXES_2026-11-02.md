# Security & Stability Fixes — 2026-11-02

This record closes the corrective actions from the 2026-11-02 public-page review. Changes were designed to preserve public UI, routes and application behavior while tightening release provenance, browser policy and runtime reproducibility.

## Workshop News

Problem:
- Production had been uploaded from divergent feature commit `908962735786783d8719ca8e30901ea0ace0b7f8`.
- That commit's Workshop News security/build workflow was red.
- The live change itself was small and safe: fixed `/kids` redirect plus two Workshop Kids links.

Corrections:
- Moved only the Kids redirect/navigation changes into `main`.
- Added explicit tests for `/kids`, including open-redirect-style query input and unsupported methods.
- Immutable artifact gate passed at commit `9256ab15f56264a5c8d29b8dac3f968bad7f0280`.
- Preview deployment: `413a6cbe-0c61-4642-acce-101c550b14ca` — success.
- Preview/production embedded bundle SHA-256: `633f42a4b4d2af7e8b0a2a202cfc93b48c9e3c9986ccdc8e2c3a818c3426da67`.
- Production deployment: `fec29857-f0d0-4cff-97cb-2ac82e23abe6` — success.
- Production trigger now records branch `main`, commit `9256ab15f56264a5c8d29b8dac3f968bad7f0280`, dirty=false.
- Previous production rollback: `6a1989e0-9952-4eef-8255-848d847ef4b7`.
- Canonical Browser Rendering smoke confirmed Workshop News 2.0 with Fake, Workshop Kids and Protocolo Ruby present.

Relevant source commits:
- `46613abbbc5a1d8b155fdb091400d124cb54dedf` — fixed Kids redirect.
- `6d583ae14e2ab70db4b0ba2db70198f777e2a668` — Kids navigation.
- `9256ab15f56264a5c8d29b8dac3f968bad7f0280` — Kids redirect/navigation security tests.
- Artifact gate run `41504471263` — success.

## Protocolo Ruby

Problem:
- Browser CSP allowed `script-src 'unsafe-inline'` and `style-src 'unsafe-inline'`.
- HSTS was absent from the public Worker.
- Live Worker source was not versioned as its canonical Cloudflare entrypoint.

Corrections:
- Versioned the live Cloudflare Worker at `protocolo-ruby/cloudflare/worker.js` on `feature/protocolo-ruby-v0.1`.
- Replaced inline-script/style permission with exact SHA-256 CSP hashes:
  - script: `sha256-4kbFbtINGWCBwWrSFNuQGGSi0YcxQE9dnHH1FekpsRg=`
  - script: `sha256-ywIE6S7DOh6BblThwUtRuJh8SRErE63NRpK1QLmIdzg=`
  - style: `sha256-LlvwOQxS2xgCsD0iIzHgiMaQSFNotzvjAl5pOFqmFpE=`
- Added `upgrade-insecure-requests`.
- Added HSTS: `max-age=31536000; includeSubDomains`.
- Kept fixed GET-only backend routes and fixed Render origin.
- Added dedicated Cloudflare Worker security tests and workflow.
- Final security-gate runs `41505219615` and `41505231084` — success.
- Production source SHA-256: `ec7b142f67ccaf640b912d3a5486d22fcc5ee9dafc2bba9da4457f29ab42ba2d`.
- Production deployment: `1d24dead-d736-4f66-9f89-979667f823ba`.
- Production version: `adc1ead1-3167-4904-bbbf-97ab9fb4c4e8`.
- Previous rollback deployment: `8facab3a-ac71-4e05-bb5b-e720f6a2b2b0`.
- Compatibility date pinned to `2026-11-02`.
- Observability remains enabled with query-string redaction.
- Post-deploy source inspection confirms zero `unsafe-inline`, expected hashes and HSTS.
- Cloudflare Issues summary after deployment: zero active issues.

Feature-branch hygiene:
- Backup: `backup/protocolo-ruby-pre-gitlink-cleanup-20261102`.
- Removed orphan gitlinks `The Ouroboros Project ` and `Wolfpack-Lair`.
- Cleanup commit: `d55f757edea6ff34887153fbcf2692db69e37211`.

## WolfPack OS

Problem:
- Public Worker had no explicit compatibility date.
- `/cerberus-gatekeeper.html` used `script-src 'unsafe-inline'` and `style-src 'unsafe-inline'`.
- Production had evolved to a nine-asset bundle while the canonical Git source still represented the older five-asset release.

Corrections:
- Gatekeeper CSP now uses exact hashes:
  - script: `sha256-O2eBRx9qu4OEbJaM8WFJNDs03FHyBFuezVrMZMuBJ5o=`
  - style: `sha256-s7AADpU2jkvAxeSluZH2IQ1HOnCjp3SI4A05ch9Po28=`
- Gatekeeper also denies connect, image, font and object sources and retains frame/form/base restrictions.
- Compatibility date pinned to `2026-11-02`.
- Observability remains enabled with 0.02 sampling and query-string redaction.
- Production deployment: `41b14649-516d-434c-a739-704bd8943cc2`.
- Production version: `81c18a2f-7463-4c6f-b1e9-f824f1a12235`.
- Previous rollback deployment: `8f848fef-8a8a-4d59-8c36-4ad2e3691b2a`.
- Cloudflare Issues summary after deployment: zero active issues.

Canonical production synchronization:
- The hardened live Worker was retrieved in bounded chunks to avoid connector truncation.
- Git source now contains the complete nine-asset production bundle.
- Sync commit: `30a5249e51adb71b39bf0307cd6dfbf0a1051068`.
- Production asset contract updated at commit `f54637a17e2b2fe7fa63ec781409b4100b76f9fa`.
- Final gates:
  - WolfPack Ruby CSP security and regression gate `41507099575` — success.
  - WolfPack OS v0.4.1 release gate `41507099618` — success.

Nine production asset hashes are locked by `web/wolfpack-os-v041-edge/worker.test.mjs`, including Logic Forge and Cerberus Gatekeeper.

## Safety / rollback

A pre-change repository backup exists:
- `backup/pre-security-stability-fixes-20261102`

Every production change above retained an immediately previous Cloudflare deployment/version as rollback evidence.

## Final state

- Workshop News production is tied to a tested `main` commit rather than the divergent feature branch.
- Protocolo Ruby no longer relies on `unsafe-inline` and now serves HSTS.
- WolfPack Gatekeeper no longer relies on `unsafe-inline`, compatibility behavior is pinned, and its nine-asset live bundle is canonical in Git.
- No user-facing redesign, route removal or intentional application-behavior change was introduced by these fixes.
