# ARGUS — Security release review (2026-10-30)

## Scope

Branch: `fix/argus-behavioral-api-hardening-20261030`

- Correct repeated brute-force alerts in one continuous failure window.
- Validate query `limit` in read-only API (alerts 1..500, timeline 1..2000).
- Add `Cache-Control: no-store`, `X-Frame-Options: DENY` and
  `Referrer-Policy: no-referrer`.
- Add behavioral/API regressions, CLI smoke checks and scoped GitHub Actions CI.
- Keep default bind address at `127.0.0.1` and avoid changing storage schema.

## Evidence

- GitHub Actions push run:
  https://github.com/kingmaker-lab/The-Workshop./actions/runs/41093327340
- Python 3.12; regression suite: **PASS — 12/12 tests**.
- CLI smoke: **PASS — 17 records processed, 3 alerts emitted**.
- API hostile-input checks: **PASS** for duplicate, negative, zero,
  non-integer and over-maximum query limits in the included regression suite.
- Header regression check: **PASS**.
- ASan/UBSan: **NOT APPLICABLE** to this Python-only patch.
- Independent penetration test and load test: **NOT TESTED**.
- Public website/security check: **NOT APPLICABLE**; no website altered.
- Cloudflare deployment: **NOT ATTEMPTED**.
- External HTTP verification: **NOT TESTED**; no public service deployed.

## Threat model and residual risks

- Logs are untrusted input. Large files and oversized or deeply nested event
  fields are not constrained at ingestion; memory/disk exhaustion remains possible.
- Source data and alerts can contain sensitive user, host and network details.
  SQLite files require operating-system access controls and secure retention.
- The read-only HTTP API has no authentication or per-client rate limit.
  Do not bind to non-loopback interfaces or expose it behind a public reverse
  proxy without an independent security design and access controls.
- Correlation state is in-memory per analysis run, not persisted between runs.
- Event ordering, time skew, high-cardinality IPs and large source populations
  need additional scale and adversarial tests.

## Release decision

**LAB ONLY**. No public service exposure is approved. GitHub Actions provides
automated regression evidence, but human review and a separate release gate
are required before promoting this patch to a publicly deployed service.

Recorded by: ChatGPT-assisted development, pending human review.
