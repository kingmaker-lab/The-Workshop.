# Security Review — ARES v0.3 / Workshop Labs

Date: 2026-10-19
Scope: activation of parser v0.2 in a real local TCP server, new Responses & Routing v0.3, website documentation and Pages Worker hardening.

## Results

| Verification | Result | Evidence |
| --- | --- | --- |
| v0.3 build with warnings as errors | PASS (local) | C17 gcc, -Wall -Wextra -Wpedantic -Werror |
| HTTP server real-socket integration tests | PASS (local) | 16/16 tests |
| AddressSanitizer + UndefinedBehaviorSanitizer | PASS (local) | 16/16 v0.3 tests in instrumented build |
| Website source / configuration security checks | PASS (static review) | 12/12: CSP, scripts, frames, methods, 404, links, crypto redirect, HTML routes, nosniff/privacy |
| GitHub CI security workflow | CONFIGURED, NOT VERIFIED | workflow defined; no successful run independently confirmed |
| Cloudflare Pages production deployment | SUCCESS | deployment id 7a42d37f-e67e-458a-8b16-131392b67238 |
| Public homepage rendering | PASS | Cloudflare Browser Rendering returned expected Workshop Labs HTML |
| Public ARES v0.3 rendering | PASS | Cloudflare Browser Rendering returned expected Responses & Routing HTML |
| Full route-by-route HTTP and headers verification | INCOMPLETE | Browser Rendering rate-limit 429 on additional requests |
| Public C server release | NOT ATTEMPTED | C binary stays loopback-only; Pages hosts documentation |

## Controls observed

- HTTP parser v0.2 linked into local v0.3 server, with bounded buffers and invalid-input rejection.
- Static routes, GET/HEAD allowlist, generic non-reflective 404/400/405/431/501, HTTP Content-Length and Connection: close.
- Local-only bind to 127.0.0.1; 5-second overall header read deadline plus socket I/O timeouts.
- Pages Worker: GET/HEAD only; unknown paths 404; fixed Crypto Labs redirect; uniform security headers for HTML, CSS, JS, icons and errors.
- Page CSP allows same-origin external script only, blocks inline/eval JavaScript, blocks framing and network connections; no external JS dependencies. Includes HSTS, nosniff, frame protections, referrer/permissions headers and cross-origin restrictions.

## Residual risks

1. Single-thread blocking local C server; not designed for internet availability or denial-of-service resistance.
2. Incomplete HTTP framing and Host validation; request smuggling security not proven; no HTTP body/pipelining/chunked.
3. The Pages Content-Security-Policy currently allows inline *styles* for inherited markup. Refactor styles before claiming a stricter CSP.
4. CI run status not independently verified; full public response-header audit not finished because Browser Rendering rate-limited the requests.
5. Build/runtime depends on system C toolchain; continuous dependency/toolchain patch review still required.

## Decision

**ARES C v0.3: APPROVED FOR LOCAL LAB ONLY. NOT APPROVED FOR INTERNET EXPOSURE.**

**Workshop Labs site: documentation update published** on existing Cloudflare Pages project, with successful deployment and limited public rendering checks. The available evidence is not a zero-risk guarantee.

Every subsequent implementation must repeat the checklist in [SECURITY_RELEASE_GATE.md](../SECURITY_RELEASE_GATE.md).
