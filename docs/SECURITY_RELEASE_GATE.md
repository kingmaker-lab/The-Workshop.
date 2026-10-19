# The Workshop — Mandatory Security Release Gate

**Permanent rule:** every new implementation, new route, dependency, or site release requires a security check **before publication**, with evidence and a documented release decision. No project may be called risk-free.

## Checklist per version

1. **Review the diff:** routes, input handling, protocol framing, filesystem, dependencies, secrets, privilege changes.
2. **Build + test:** compile with warnings-as-errors; regression tests; boundaries and hostile inputs; C sanitizers (ASan/UBSan).
3. **Threat model:** internet vs local exposure, untrusted data, resource constraints, new attack surfaces, privilege boundaries.
4. **Adversarial cases:** malformed HTTP, too many/large headers, request smuggling and leftover bytes, method allowlist, slow clients, XSS, traversal and injection when relevant.
5. **Cloudflare web app:** check home, ARES, all version pages, Crypto Labs redirect, 404/405, GET/HEAD, security headers, CSP, clickjacking, no secrets or dynamic HTML reflection, safe external links.
6. **Dependencies / infrastructure:** inventory, least privileges, secrets, exposed ports, error logging and relevant patch levels.
7. **CI:** code tests, sanitizers and website checks pass. If CI unavailable, record manual evidence and limitations.
8. **Post-deploy:** verify Cloudflare deployment status AND actual HTTP responses/security headers on public URLs. A successful deploy is not proof that pages work correctly.
9. **Record:** scope, tests, results, risks, release decision, reviewer/date.

## Release record template

    Version:
    Scope:
    Build/tests: PASS | FAIL | NOT TESTED
    ASan/UBSan: PASS | FAIL | NOT TESTED
    Web security check: PASS | FAIL | NOT TESTED
    Cloudflare deploy: SUCCESS | FAILED | NOT ATTEMPTED
    External HTTP verification: PASS | FAIL | NOT TESTED
    Known risks:
    Public C server exposure: NO unless separately approved
    Decision: LAB ONLY | BLOCKED | CONDITIONAL APPROVAL

Cloudflare Pages hosts only the website/docs. The local ARES HTTP executable must not be exposed directly without hardened deployment design, concurrency, precise framing and independent security review.

Repeat this check for **every subsequent version**. Keep the checklist in the repository so it survives conversation/session changes.
