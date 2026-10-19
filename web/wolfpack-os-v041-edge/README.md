# WolfPack OS v0.4.1 — official cards release

## Change
- ARES card opens `https://workshop-labs.pages.dev/projects/ares/`.
- CERBERUS card opens `https://cerberus.wolfpackworkshop.workers.dev/`, correctly described as **Software Architecture Lab**, not orchestration.
- Both cards use semantic HTML links, `rel="noopener noreferrer"`, `referrerpolicy="no-referrer"`, and visible keyboard focus.

## Source and fidelity
Built from the user's complete original `wolfpack-workshop-cloudflare-v0.4-raven.zip`, not the older v0.3 repository HTML. Only two card elements and a small accessibility style are changed. The five inline script elements and the four other assets (Ruby WASM worker JS + three ZIP downloads) were preserved byte for byte. See `MANIFEST.json` for their SHA-256 digests.

The deployed Worker `worker.mjs` is a self-contained read-only HTTP server containing these five assets as base64 literals. This avoids replacing v0.4 assets with obsolete v0.3 assets and avoids reliance on the Cloudflare assets upload JWT flow, which the current integration cannot complete. **The base64 constants are static public resources, not secrets.**

## Routes
- `/`, `/index.html`: WolfPack v0.4.1 HTML
- `/js/ruby-worker.js`: unchanged Ruby WASM loader
- `/downloads/raven-ruby-v0.1-original.zip`
- `/downloads/vulpes77-terminal-v0.1-original.zip`
- `/downloads/wolfpack-ruby-protocol-v0.1.zip`

GET and HEAD supported. Other paths return 404; unsupported methods return 405. ETags permit 304, static resource responses have explicit cache headers. Security headers: HSTS, CSP with SHA-256 hashes for the three executable inline scripts, X-Frame-Options DENY, nosniff, Referrer-Policy no-referrer, Permissions-Policy restrictive. Existing CDN dependencies (Google Fonts and jsDelivr Ruby WASM) remain unchanged.

## Test locally
```bash
node --test web/wolfpack-os-v041-edge/worker.test.mjs
```

## Deployment
Upload `worker.mjs` using Cloudflare Workers API as a new version of `wolfpack` with `main_module: "wolfpack-v041.mjs"`, `compatibility_date: "2026-10-19"`, and **no `keep_assets` setting** (this release bundles all assets). Activate after acceptance tests. The v0.4.0 Worker version `53fcb16b-5a66-432f-abeb-1611cd4866b1` remains rollback target.

## Limitations
Preserving bytes and passing unit tests does not prove complete browser behavior. Verify Ruby Protocol, VULPES-77, RAVEN, responsiveness, all downloads, and actual response headers after deployment. Future releases should move back to Cloudflare Static Assets with a reproducible CI build and staged deployment when asset-upload credentials support it.
