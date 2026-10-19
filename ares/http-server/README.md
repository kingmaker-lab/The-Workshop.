# ARES v0.4 — Static Files

> Build. Break. Understand. Rebuild.

This stage extends the local HTTP/1.1 server from v0.3 with controlled static files. The v0.2 HTTP header parser, GET/HEAD routes and response serializer remain integrated.

**Scope: LAB ONLY. C server stays on 127.0.0.1. Cloudflare Pages publishes documentation, not the C executable.**

## Build, test and run

From the Workshop repository root:

    make test-ares-http
    make test-ares-server
    make run-ares

Or:

    cd ares/http-server
    make clean && make test
    make run

The local server starts at http://127.0.0.1:8080 (tests use a random loopback port).

    curl -i http://127.0.0.1:8080/health
    curl -i http://127.0.0.1:8080/static/index.html
    curl -i http://127.0.0.1:8080/static/assets/site.css
    curl -I http://127.0.0.1:8080/static/index.html

Its trusted local document root is **ares/http-server/public/** relative to its working directory. The Makefile runs from that directory. When launching manually, cd there first.

## v0.4 pipeline

    accept() -> recv() -> HTTP Parser v0.2 -> Router
                                             |
                  GET /, /about, /health ----+
                                             |
                  /static/* -> URL allowlist -> public/ fd
                               -> openat() every segment with O_NOFOLLOW
                               -> fstat(): regular file and size <= 256 KiB
                               -> extension/MIME allowlist
                               -> response stream (read/send in 16 KiB chunks)

**No URL decoding.** Static paths allow only ASCII letters, digits, underscore, dash, dot (not leading a segment) and slash separators. Any dot component, encoded path, query, backslash, hidden item, repeated slash, empty component or unknown extension fails closed with generic 404.

### MIME types

| Extension | Content-Type |
| --- | --- |
| html | text/html; charset=utf-8 |
| css | text/css; charset=utf-8 |
| js | text/javascript; charset=utf-8 |
| json | application/json; charset=utf-8 |
| txt | text/plain; charset=utf-8 |
| svg | image/svg+xml |
| png | image/png |
| jpg, jpeg | image/jpeg |
| webp | image/webp |
| ico | image/x-icon |

Files must physically exist below trusted public directory. Files over 256 KiB return generic 403. Files missing, symbolic links, directories, FIFOs and unsupported types return 404. GET/HEAD only. There is no automatic index resolution: use /static/index.html, not /static/.

## Mandatory security check-up: 2026-10-19

**33/33 real-TCP integration tests passed locally** in both normal and AddressSanitizer + UndefinedBehaviorSanitizer builds.

Coverage includes:
- Regression of old HTTP routes and error statuses.
- MIME types: HTML, CSS, JSON and PNG bytes.
- HEAD with no body and Content-Length of equivalent GET.
- Nested directories, 256 KiB boundary and oversized-file refusal.
- Dotdot traversal, percent encoding, backslash, double slash and hidden paths.
- Symlinks in final and intermediate components pointing outside document root.
- FIFOs and directories refused without blocking.
- Unknown extensions, 404, 403, and POST -> 405.

Sanitizer results are evidence from tested paths, not proof of absence of defects.

### Known risks / blocking reasons for public exposure

1. public/ must be trusted and not writable by network clients; bind mounts, hardlinks, attacker-writable ancestors and racing modifications require further hardening. Do not expose user-uploaded assets through this endpoint.
2. Single blocking client per process; no scheduling, adaptive timeouts, rate limits or resource limits for internet DoS.
3. HTTP parser v0.2 is incomplete: no bodies, chunked, complete Host grammar or pipelining; it cannot guarantee request-smuggling resistance, and extra bytes may arrive after header parsing.
4. File content can change between stat and read: the 256 KiB limit is based on original descriptor metadata; root stability is a deployment requirement.
5. HTML/SVG/JS are active content. The static root must not accept public user uploads or unreviewed content.
6. No TLS, privilege drop, process sandbox, internet deployment, audit-grade logging or independent penetration test.

**Decision: LOCAL LAB APPROVED, PUBLIC C SERVER RELEASE BLOCKED.**

## Sanitizer command

    cd ares/http-server
    make clean
    make test CFLAGS='-std=c17 -O1 -g -Wall -Wextra -Wpedantic -Werror -fsanitize=address,undefined -fno-omit-frame-pointer' LDFLAGS='-fsanitize=address,undefined'

## Future work

v0.5 — Concurrency, epoll, backpressure and slow clients. Treat complete HTTP framing as a blocking dependency before any internet deployment.

The release process is documented at ../../docs/SECURITY_RELEASE_GATE.md. Repeat the security check after every subsequent change.

[Workshop Labs — ARES](https://workshop-labs.pages.dev/projects/ares/).
