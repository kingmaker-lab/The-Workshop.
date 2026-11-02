# Hardening applied — 2026-11-02

This record documents additive security and stability changes applied without changing public routes, UI, educational content, CTF rules or the existing application architecture.

## 1. Distributed rate limiting

### Workshop Kids

Bindings:
- `KIDS_API_LIMITER`: 30 requests / 60 seconds per route-scoped client key.
- `KIDS_AI_LIMITER`: 8 model-assisted requests / 60 seconds per mascot/client key.

Protected surfaces:
- `POST /api/heart`
- `POST /api/blade`
- optional Workers AI inference for Heart and Blade.

The pre-existing in-memory limiter remains active as a second layer. Rate limiter failure does not take the educational portal offline; the existing guided response path remains available.

Current production deployment:
- deployment: `7c28502e-7d64-4d5b-9245-22f08190645e`
- version: `65991f9f-f8bb-4371-9504-257daf90923f`
- rollback: `1bc5051c-c12a-4599-8e53-6f057fd5fe6c` / version `c95b8f79-38c7-4daf-b62d-268a2c088550`

Validation:
- Workshop Kids source gate: `41469019387` — success.
- Workshop Kids live smoke: `41469019100` — success.
- Cloudflare Browser Rendering after final deployment confirmed the public Workshop Kids home with Heart and Blade.

### Security Division / CTF

Bindings:
- `CTF_AUTH_LIMITER`: 8 session/restore attempts / 60 seconds per route-scoped client key.
- `CTF_SUBMIT_LIMITER`: 40 flag submissions / 60 seconds per client key.

Protected surfaces:
- `POST /api/session`
- `POST /api/restore`
- `POST /api/submit`

The existing per-player submission limiter remains active. D1 remains parameterized and the existing `FLAG_SECRET` binding was preserved.

Final production artifact:
- CI run: `41469346425` — success.
- artifact id: `13154736877`
- artifact Worker SHA-256: `b594bf7a4b1958bc48cb3b3a8b0a3dd413ecddaba24c73f1a99d7ce0e2359eb0`
- Cloudflare deployment: `82782b19-f2dc-4b3f-9b43-bf019a05e47a`
- version: `5fd7adbc-4df0-4eda-a07a-e8809028bfe4`
- rollback: `40947604-2b1f-4809-9cc7-0854345e9fde` / version `35f4c426-23a1-4e8c-8850-3b75b22f6f0b`

The deployed script was promoted only after the derived live bytes matched the CI artifact SHA-256 exactly. `/api/health` returned `{"status":"ok"}` after promotion.

## 2. Reproducible Pages Direct Upload

Added:
- `scripts/pages-release.mjs`
- `.github/workflows/pages-artifact-gate.yml`
- `.github/workflows/pages-promote.yml`
- `docs/PAGES_RELEASE_PROTOCOL.md`
- `docs/PAGES_ROLLBACK_BASELINE_2026-11-02.md`

Flow:
`commit → source tests → immutable artifact → file hashes + aggregate hash → preview → smoke → same bytes to production → smoke → rollback evidence`

The production Pages projects were **not redeployed** as part of establishing this flow.

Current rollback baselines are recorded for Workshop News, Workshop Labs and WolfPack Crypto.

Workshop News 2.0 production source was synchronized into `main` at `sites/workshop-news/` using the exact Git blobs from the production commit `59a5b92f5dca1a7e76e8766d1e7c70555b06bf55`. The release builder includes the complete current asset set, including Fake/Fake Walker/Fake 3D assets.

Final immutable artifact gate:
- run `41470341207` — success.
- commit `d215ef95fc9ad0480783173376def24d806d34d8`.
- Workshop News artifact: `13153708614`.
- Workshop Labs artifact: `13154138199`.
- WolfPack Crypto artifact: `13154287858`.

Promotion requires the repository secrets `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`; the workflow itself does not expose credentials.

## 3. Privacy-safe observability

Cloudflare Workers Observability is enabled with query-string redaction and Issues for:
- workshop-kids — sample 0.10
- workshop-security — sample 0.10
- workshop-discord — sample 0.10
- protocolo-ruby — sample 0.10
- cerberus — sample 0.02
- wolfpack — sample 0.02

Invocation logs provide status/outcome and runtime latency without application code logging request bodies.

Application telemetry added:
- Kids rate-limit events: scope only.
- Kids AI failure events: mascot/AI scope only.
- CTF rate-limit events: scope only.
- CTF D1 failures: event + route only; the D1 exception text, SQL, bindings, flags, recovery codes, sessions and request body are not logged.
- generic CTF API failures: event + route only.

`redact_query_string=true` is enabled in Cloudflare settings.

## 4. Repository gitlink cleanup

Removed orphan gitlinks:
- `The Ouroboros Project `
- `Wolfpack-Lair`

No real project directory was deleted.

Safety:
- backup branch: `backup/pre-gitlink-cleanup-20261102`
- cleanup commit: `c0e2f61a02cdf06ac05148c093935c3248f89f92`
- current recursive main tree: zero mode-160000 gitlinks.

Subsequent Actions checkout logs no longer emit the previous missing-`.gitmodules` fatal warning.

## Result

Public application structure and visible behavior were preserved. Hardening is additive: distributed abuse controls, immutable releases, privacy-safe observability and repository hygiene.
