# Protocolo Ruby v0.3 · Private async API prototype

This prototype adds a private bearer-token API and Sidekiq/Redis job queue for **static** analysis only. It does not execute samples. No Cloudflare route is connected to this service.

## WARNING: infrastructure scaffold, not a production deployment

- The compose file intentionally does not connect the worker to any network. **This also prevents it from reaching Redis and therefore it cannot process jobs as written.** This is a fail-closed reference configuration; deployers must design a controlled internal-only channel before enabling jobs.
- There is no auth rate limiting, encrypted transient sample storage, anti-malware parser hardening, tenant isolation or independent security assessment yet.
- Never expose port 9293 publicly or route browser uploads to this service in its current state.
- Use only synthetic test data until isolation and resource limits have been reviewed.

## API contract
- GET /health (local health check)
- POST /v1/analyses (Bearer token, application/octet-stream, max 20 MiB) => 202, UUID
- GET /v1/analyses/:id => current status and report; access controlled with the same Bearer token

Next: implement a constrained network path between Redis and worker; remove any dangerous implicit networks; run integration tests; protect the API behind Cloudflare Access before any production enablement. YARA-X remains an optional offline adapter.
