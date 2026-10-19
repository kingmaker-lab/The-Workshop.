# ARES v0.3 — Responses & Routing

> Build. Break. Understand. Rebuild.

**Status:** local lab only. The real TCP transport is now linked with HTTP Parser v0.2 and the v0.3 router/response serializer.

## Build and run

From the Workshop root:

    make test-ares-http
    make test-ares-server
    make run-ares

Or:

    cd ares/http-server
    make test
    make run

Then from another terminal:

    curl -i http://127.0.0.1:8080/
    curl -i http://127.0.0.1:8080/health
    curl -i http://127.0.0.1:8080/about
    curl -I http://127.0.0.1:8080/health

Use ./build/ares --port 0 to request an ephemeral port. The server always binds to **127.0.0.1**, never 0.0.0.0.

## Architecture

    socket() → bind(127.0.0.1) → listen() → accept()
      → recv() → ares_parser_feed() → ares_route()
      → ares_write_response() → close()

The parser receives arbitrary TCP fragments, recognizes CRLF CRLF, rejects malformed requests, and produces a validated request structure. Routing is static. Responses serialize status, date, Content-Type, Content-Length, Connection: close, Cache-Control: no-store, nosniff, X-Frame-Options and Referrer-Policy.

| Method | Path | Result |
| --- | --- | --- |
| GET | / | 200 plain text |
| GET | /health | 200 static JSON |
| GET | /about | 200 project description |
| HEAD | same paths | headers, empty body |
| GET | others | 404 |
| POST etc. | any path | 405; Allow: GET, HEAD |

Malformed header → 400; timeout → 408; too many or too-large headers → 431; unsupported body framing → 501. One request per connection.

## Security check-up v0.3

**16 real-socket integration tests passed locally** on the normal build and with AddressSanitizer + UndefinedBehaviorSanitizer. Parser v0.2 tests are separate.

Implemented controls:
- Loopback-only bind.
- Parser bounded to 8192 header bytes, field and count limits.
- Monotonic 5-second read deadline plus per-operation socket timeouts.
- SIGPIPE ignored; bounded response header serialization; retry for interrupted/partial sends.
- GET and HEAD allowlist; generic non-reflective errors; no filesystem, commands, templates or dynamic HTML.
- Coherent Content-Length (including HEAD), no-store, nosniff and anti-framing headers.

**Known risks / blockers to internet exposure:**
- A single blocking connection can delay the whole server; no concurrency or connection quotas.
- Read deadline does not bound all response writing or client queues.
- The parser is deliberately incomplete: no body, chunked transfer, full Host grammar, pipelining or request-smuggling guarantee.
- Extra bytes received with headers are rejected, but later bytes can go unnoticed before close. Closing with unread data can cause TCP RST.
- No TLS, auth, rate limiting or hardened reverse proxy.
- Invalid HEAD requests can return an error body because method validation failed.
- HTTP/1.0 input may receive HTTP/1.1 response; not a complete HTTP stack.

**Security release decision:** approved for local experiments ONLY. Not approved for public exposure.

## Run sanitizers

    cd ares/http-server
    make clean
    make test CFLAGS='-std=c17 -O1 -g -Wall -Wextra -Wpedantic -Werror -fsanitize=address,undefined -fno-omit-frame-pointer' LDFLAGS='-fsanitize=address,undefined'

See: ../../docs/SECURITY_RELEASE_GATE.md for the mandatory security checklist. Cloudflare Pages hosts project documentation and **does not run this C server**.
