# ARES v0.4 — Security Check-Up / Release Decision

Date: 2026-10-19
Target: C HTTP server v0.4 plus Workshop Labs documentation.
Scope: secure static file resolution, MIME mapping, bounded file responses, regression of v0.3 TCP/HTTP behavior.

## Local evidence

| Test | Result | Evidence |
| --- | --- | --- |
| C17 compile with -Wall -Wextra -Wpedantic -Werror | PASS | local GCC 14 |
| Real TCP end-to-end integration suite | PASS 33/33 | local unittest, dynamic loopback port |
| AddressSanitizer + UndefinedBehaviorSanitizer | PASS 33/33 | second instrumented local run |
| Request traversal tests (dotdot, percent encoding, backslash) | PASS | tests/test_http_server.py |
| Intermediate/final symbolic-link escapes | PASS | tests/test_http_server.py |
| FIFO, directories, unknown MIME and hidden items | PASS | tests/test_http_server.py |
| File cap at 256 KiB, HEAD, MIME types | PASS | tests/test_http_server.py |
| Cloudflare source security inspection | PENDING | run website test and pre-deployment review |
| Cloudflare deploy | PENDING | fill after publication |
| Public URL/headers verification | PENDING | fill after publication |
| Public deployment of C binary | NOT AUTHORIZED | localhost only |

## Implemented boundaries

- No file path derived by joining an untrusted raw URL to a filesystem path.
- Strict component allowlist with no URL decoding, no dot or hidden components.
- Trusted directory fd + openat each component with O_NOFOLLOW.
- No regular-file bypass: O_NONBLOCK prevents FIFO open from hanging, fstat ensures S_ISREG.
- Size cap based on fstat (maximum 256 KiB) before streaming, 16 KiB chunks.
- Only GET and HEAD; static MIME allowlist; generic failures with no path leaks.
- Close file fd after serving, including HEAD; no dynamic HTML/JS injection from request.

## Residual risks

- Trusted root must not be user-writable; special bind mounts, hardlink scenarios and racing content changes are out of the lab's threat model.
- v0.2 parser is incomplete: framing, body handling, and request smuggling hardening unfinished.
- Single blocking client, no concurrent limit/rate limits. Slow-client and backpressure control missing.
- Content-Length refers to fstat size, so concurrent truncation may yield incomplete transfer.
- Active file types HTML/SVG/JS only safe when content is reviewed and trusted.
- No process privilege isolation or TLS; internet exposure remains prohibited.
- Web CSP currently uses unsafe-inline for styles for existing pages. Script CSP stays same-origin only; improving stylesheet policy is pending.
- A successful Cloudflare deployment does not prove that every public route and security header was verified.

## Release decision

**ARES C v0.4: APPROVED ONLY FOR LOOPBACK LOCAL LAB. PUBLIC C SERVER: BLOCKED.**

**Workshop Labs documentation:** may be published after regression checks. Fill Cloudflare deployment and public checks in this record following release.

Follow the permanent instructions in docs/SECURITY_RELEASE_GATE.md for every future implementation.
