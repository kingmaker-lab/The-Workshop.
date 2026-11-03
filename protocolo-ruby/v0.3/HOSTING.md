# Protocolo Ruby · Hosting readiness

## Current Cloudflare account blocker

On 2026-10-30, the Cloudflare Containers API returned HTTP 401 with the explicit message: `Deploying containers requires the Workers Paid plan`. Therefore **no Ruby container was deployed**. The existing public Worker runs browser-only JavaScript inspection, not this backend.

## Recommended architecture

- Frontend: Cloudflare Worker (already deployed).
- Private ingress: authenticated Cloudflare Access + Worker service binding / authenticated backend request.
- Runtime: Ruby API and Sidekiq worker in a provider-supported container environment.
- State: Redis reachable only on a private network, no external port.
- Samples: temporary, encrypted, short-lived; prohibit arbitrary sample downloads and logs.
- YARA-X: optional only within an isolated static-analysis worker, with CPU/memory/time limits.

## Before publishing API

1. Review dependencies and build reproducible OCI images from pinned versions, with an SBOM.
2. Run Ruby tests, HTTP/API integration tests and end-to-end queue tests using **synthetic fixtures only**.
3. Add real rate limits, global queue backpressure, worker hard timeouts, per-user authorization and audit logs.
4. Ensure the worker cannot execute samples and does not have outbound Internet access.
5. Replace Redis-held raw samples with a dedicated encrypted temporary ingestion store.
6. Confirm secure worker-to-queue communications and verify data lifecycle/deletion.
7. Protect the ingress using Cloudflare Access and do not embed a shared Bearer token in browser JavaScript.
8. Validate isolation using an independent security review before any public sample upload.

## Running locally

The v0.3 Compose and Rack code are experimental scaffolding, not a turnkey production deployment.
The API is intended to bind only to `127.0.0.1:9293`. Do not expose it via port forwarding, Cloudflare Tunnel or any public endpoint until the safeguards above are complete.

## Cloudflare Containers

If the account enables Containers and the deployment is validated, build/push the Ruby OCI image and configure a dedicated container-backed Worker. Avoid deploying the existing local WEBrick server directly into a public Worker runtime.
