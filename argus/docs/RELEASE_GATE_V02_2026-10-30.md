# ARGUS v0.2 and Workshop Labs: release gate — 2026-10-30

## Scope

- ARGUS: opt-in statistical anomaly detector on numeric Zeek events.
- Workshop Labs: ARGUS card on homepage plus static `/argus/` research page.
- No public ARGUS API deployment. No event ingestion from browsers.

## Verification

- ARGUS regression tests, Python 3.12: **PASS 17/17**.
  https://github.com/kingmaker-lab/The-Workshop./actions/runs/41095180333
- Workshop Labs static Worker smoke tests, Node 22: **PASS 4/4**.
  https://github.com/kingmaker-lab/The-Workshop./actions/runs/41095180501
- ARGUS CLI smoke (sample): **PASS**, 17 input events and 3 alerts.
- Cloudflare Pages `workshop-labs` preview deployment:
  https://11cf9c02.workshop-labs.pages.dev
  Deployment stage: **SUCCESS**. External HTTP validation: **NOT VERIFIED**;
  browser rendering attempts were rate-limited. Verify after production deployment.
- ASan/UBSan: **NOT APPLICABLE** to Python/JavaScript changes.
- Manual pentest and scale tests: **NOT TESTED**.

## Threat model / residual risk

- Baseline drift, attack-driven contamination, false positives and lack of model
  persistence between analysis runs.
- Ingestion of high-cardinality untrusted `source` values can grow memory usage;
  no ingestion-time quotas are implemented.
- No unattended decision/action on statistical outliers; human review required.
- Web page includes static descriptions only, no browser API calls or live logs.
- ARGUS remains local-first with `127.0.0.1` API default. Do not expose
  the API remotely without independent authentication/authorization and review.
- Existing strict CSP, no third-party scripts and deterministic 404/405 preserved
  by Workshop Labs worker test suite.

## Decision

- ARGUS engine: **LAB ONLY**, code release approved after CI.
- Workshop Labs static research page: **CONDITIONAL PUBLICATION**, subject to
  Cloudflare deployment success and production HTTP verification.
- Workshop News: preserve existing deployment until its source and assets can
  be safely updated.

Reviewer: automated checks plus ChatGPT-assisted diff review; human review encouraged.

## Production follow-up — 2026-10-30

- Workshop Labs production deployment: `84f5384a-144a-466e-97c9-877bb7dc6f82`, **SUCCESS**.
- Browser Rendering GET `https://workshop-labs.pages.dev/argus/`: **HTTP 200**;
  expected ARGUS, Welford and static-only disclaimer were visible.
- Public website is documentation only. ARGUS processing/API not deployed.
- The earlier "External HTTP validation: NOT VERIFIED" above describes the
  initial preview attempt; the production route was checked afterward.
