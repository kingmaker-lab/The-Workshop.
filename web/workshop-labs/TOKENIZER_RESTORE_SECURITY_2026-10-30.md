# HeartAI Tokenizer Playground Restoration — 2026-10-30

## Issue
The historic HeartAI browser playground was tracked in
`IA/Heart/site/argus/index.html` and `IA/Heart/site/argus/argus.js`.
A new defensive ARGUS project used `/argus/` on Workshop Labs and the
interactive HeartAI tokenizer was no longer reachable at that path.

## Resolution
- Restore HeartAI at `/heartai/` with the original static Byte-level BPE
  demonstration and JS logic; serve script at `/heartai/tokenizer.js`.
- Add dedicated HeartAI card on Workshop Labs homepage and cross-link from
  defensive ARGUS page; `/argus/tokenizer` redirects to the new playground.
- Keep `/argus/` dedicated to defensive threat hunting without modifying its
  implementation.
- No dynamic API, credentials, remote inferencing or event ingestion added.

## Security controls and threat model
- HeartAI HTML CSP: `script-src 'self'`, `connect-src 'none'`,
  `frame-ancestors 'none'`; the inline CSS exception is limited to the
  HeartAI HTML endpoint.
- All other web endpoints retain their existing restrictive CSP. The
  tokenizer JS endpoint responds with `application/javascript`, HEAD
  support and `nosniff`. Existing 404/405 behavior and security headers
  are preserved.
- User input goes only through TextEncoder and textContent. It is
  neither evaluated as HTML nor transmitted to the server.
- The tokenizer is an educational browser demonstration trained against
  a small fixed corpus; it is not the production HeartAI model.

## Verification
- Node.js workflow: `node --test web/workshop-labs/tests/*.test.mjs`,
  8/8 PASS in the restore branch.
- Browser Rendering on Cloudflare Pages preview
  `https://d2de1dae.workshop-labs.pages.dev/heartai/`: HTTP 200,
  JavaScript executed; sample output displayed 15 characters,
  19 UTF-8 bytes, 17 tokens and 28 demonstration merges.
- Preview Pages deployment: SUCCESS.
- Manual adversarial browser penetration test: NOT TESTED.
- Existing ARGUS Python code is unchanged.

## Decision
Static public demonstration is eligible for release after CI pass.
Any future new input fields, dependencies, scripts or API integrations
require a fresh security gate. No claim of risk-free operation.
