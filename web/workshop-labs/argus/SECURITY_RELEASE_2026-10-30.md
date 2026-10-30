# ARGUS / Workshop Labs: static content release gate (2026-10-30)

## Change
The ARGUS public page now contains architecture, detection descriptions, a
synthetic 17-event / 3-alert timeline, JSON/YAML examples, local quick-start,
security caveats and a planned roadmap.

- Editorial source: `web/workshop-labs/argus/index.html`.
- Runtime mirror: `ARGUS_HTML` in `web/workshop-labs/_worker.js`.
- Automated source-mirror, route and CSP checks: `tests/argus-content.test.mjs`.

## Security boundary
Static content only: no JavaScript, forms, authentication, uploads, proxying,
live logs or network requests. Existing response CSP preserves
`script-src 'none'`, `connect-src 'none'`, `frame-ancestors 'none'`,
with the pre-existing CSS-inline exception scoped to `/argus/`.
Existing sibling laboratories are preserved. The Python ARGUS backend
remains local-only and **LAB ONLY**; do not publish its unauthenticated API.
No claim is made about production detection accuracy or live telemetry.

## Validation
Cloudflare preview `24b8e65e.workshop-labs.pages.dev/argus/` succeeded.
Browser Rendering returned HTTP 200 and confirmed all content sections.
CI and production checks are required before public promotion.
Independent pentest and screen reader audits were not performed.
