# Cloudflare → Render staging integration

Deployed 2026-10-30 to Cloudflare Worker `protocolo-ruby` at `https://protocolo-ruby.wolfpackworkshop.workers.dev`.

## Read-only gateway routes

- GET `/backend/health` → Render `/health`
- GET `/backend/capabilities` → Render `/v1/capabilities`
- GET `/backend/demo` → Render `/v1/demo`

Cloudflare proxies only these fixed endpoints, and the browser UI provides status and demo buttons. A timeout is applied to upstream requests, with no browser-origin CORS granted. No sample file leaves the browser, no upload or user-supplied URL is forwarded.

**Not production-ready:** this is a public demonstration, not secure private origin authentication. Render endpoints are publicly accessible and offer only harmless fixed synthetic data. Full asynchronous upload functionality is intentionally not connected.

Future work: Cloudflare Access, private authentication to origin, rate limiting, worker queue, hardened ephemeral encrypted sample storage, robust static parser isolation and integration tests. Ensure production frontend source is versioned as Worker module in GitHub.
