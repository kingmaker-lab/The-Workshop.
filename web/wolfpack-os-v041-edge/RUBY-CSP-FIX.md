# WolfPack OS v0.4.2 — Ruby Protocol WebAssembly CSP correction

## Report
Screenshot and reproducible Playwright execution on 2026-10-19 showed Ruby Protocol failing with **"Erro ao carregar o motor Ruby"**. The Worker entry script returned HTTP 200, then Chromium blocked:
`https://cdn.jsdelivr.net/npm/@ruby/wasm-wasi@2.10.1/dist/browser/+esm` — **requestfailed=csp**.

This was **not** a user-script syntax error or a missing /js/ruby-worker.js file.

## Root cause
The document's response CSP included:
`worker-src 'self' blob:`

The module Worker imports the fixed Ruby WASM runtime from jsDelivr. When the browser's CSP was bypassed only for diagnosis, the Ruby program `puts "A matilha despertou!"` passed its test and awarded 100 XP, confirming the runtime worked. Replacing **only** the worker-src directive in the browser with:

`worker-src 'self' blob: https://cdn.jsdelivr.net`

also passed the same Ruby mission with CSP **enabled**, with no failed requests.

## Code patch
The deployed Worker source `web/wolfpack-os-v041-edge/worker.mjs` has a one-directive change from:

`worker-src 'self' blob:;`

to:

`worker-src 'self' blob: https://cdn.jsdelivr.net;`

The source comments identify the minor release as v0.4.2. No change was made to:
- The five original application assets and their SHA-256 digests.
- Script hashes, inline script behavior or `script-src`.
- `connect-src` or external third-party runtime URLs.
- ARES/CERBERUS links, gameplay, game progress storage, ZIP downloads, VULPES-77 or RAVEN.
- HTTP routes or allowed request methods.

**Security:** this allowlists one additional origin for Worker imports instead of disabling CSP or adding `unsafe-eval`. The origin is already required by the existing pinned Ruby runtime; third-party CDN code remains part of the supply-chain trust boundary. For future hardening, vendor version-pinned runtime assets with integrity auditing.

## Gates
- `node --test web/wolfpack-os-v041-edge/*.test.mjs` for CSP, data hashes and contracts.
- Browser testing must **execute a Ruby mission** against the actual public domain, not only inspect the page.
- Recheck responsive views, VULPES-77, RAVEN, security headers and ZIP digests.
- Keep previous Worker version `b10070ca-b386-4d3d-a3f4-f55791f75206` for immediate rollback.
