# Edge Security Validation Matrix | 2026-10-30

## Scope
Workshop Labs, Crypto Lab, ARES Pages Worker, Cerberus Worker, WolfPack OS.
Shared test: node --test security/site-security.test.mjs
CI: .github/workflows/edge-security-baseline.yml

## Automated validation
1. GET/HEAD success with HEAD empty body.
2. X-Content-Type-Options: nosniff.
3. X-Frame-Options DENY and CSP frame-ancestors none.
4. CSP object-src none, base-uri none, no unsafe-eval.
5. HSTS max-age and Permissions-Policy camera=().
6. Referrer-Policy present.
7. No unsolicited Access-Control-Allow-Origin.
8. POST/PUT/PATCH/DELETE/OPTIONS -> 405; Allow GET, HEAD; Cache-Control no-store.
9. Sensitive/dot/traversal-like paths -> 404; Cache-Control no-store.
10. No query string reflection on root; no query-controlled redirects.
11. Existing per-component tests required.

## Fix applied
Crypto Lab now explicitly sends Cache-Control: no-store for 405 responses and all 404 responses, including nonexistent /assets/ paths.

## Deployment and operations not verified
HTTPS certificate/TLS validation; live deployed HTTP headers; WAF and DDoS configuration; account MFA; secret rotation; supply-chain and dependency vulnerability scans; alert delivery and audit logs; verification of Grupo AMO independent deployment.
No production Cloudflare deployment was performed by this change. Manually deployed Pages projects require an explicit, controlled deployment of the tested source.

## Release gate
Never treat NOT VERIFIED as PASS. Block release on failing CI. Test preview then production responses, record a release decision and rollback strategy.
