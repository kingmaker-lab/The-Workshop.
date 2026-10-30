# Protocolo Ruby v0.3 · Private async API prototype

This prototype adds a private bearer-token API and Sidekiq/Redis job queue for **static** analysis only. It does not execute samples. No Cloudflare route is connected to this service.

## WARNING: infrastructure scaffold, not a production deployment

- The API and worker communicate with Redis over a Docker internal-only network. The worker has no outbound Internet route, but Docker network isolation is not a hardened malware sandbox.
- There is no auth rate limiting, encrypted transient sample storage, anti-malware parser hardening, tenant isolation or independent security assessment yet.
- Never expose port 9293 publicly or route browser uploads to this service in its current state.
- Use only synthetic test data until isolation and resource limits have been reviewed.

## API contract
- GET /health (local health check)
- POST /v1/analyses (Bearer token, application/octet-stream, max 20 MiB) => 202, UUID
- GET /v1/analyses/:id => current status and report; access controlled with the same Bearer token

Next: run integration tests and dependency checks, add queue backpressure and strong sample encryption, then protect the API behind Cloudflare Access before any production enablement. YARA-X remains an optional offline adapter.
