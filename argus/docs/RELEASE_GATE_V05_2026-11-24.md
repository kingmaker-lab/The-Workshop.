# ARGUS v0.5 | Multi-host temporal correlation — security/release gate

Date: 2026-11-24
Status: **LAB ONLY for the Python engine**. Static public documentation is permitted once tests and Cloudflare preview succeed.

## Scope
- Adds `argus/detection/multihost_v05.py`, a **local, opt-in** correlator for failed authentication events keyed by normalized source IP, distinct normalized host identities (`source`) and a bounded time window.
- Default candidate: **6 failures across 3 hosts within 120 seconds**. One `multi_host_failed_auth_burst` detection (medium/30 points) per active qualifying episode, integrated into the existing scoring/alert and SQLite persistence.
- No modifications to the existing v0.1–0.4 heuristics, old Sigma subset or Welford logic when disabled. Dedicated demonstration config `config-v05-demo.yaml`; default config sets `temporal_v05.enabled: false`.
- No remote agent, webhook, log ingestion, response, cloud model, API extension, authentication backend or exposed database.
- Static Workshop Labs page displays a synthetic eight-event timeline and safe CLI instructions only.

## Threat model and mitigations
- Log sources are operator-controlled, but sample content may include attacker-originated fields. We do not execute log field content, deserialize untrusted Python objects or evaluate Python from rules.
- Only events `event_type=authentication` with `result=failed`, valid IP address and a non-empty normalized `source` identity of at most 128 characters are considered; "unknown" sources are excluded.
- Configuration is strictly typed and validated; `enabled` must be a YAML boolean. Unsupported keys fail closed. Limits: 10–3600s window, 2–16 hosts, 2–128 failures, maximum 1,024 tracked IPs and 128 retained failures per IP. Host and IP cardinality are bounded in-process.
- Duplicate `event_id` values in an active window are not counted twice. Out-of-order timestamps per IP are ignored without resetting the active window. The same burst is not repeatedly detected until it falls below threshold. The least recently observed IP state is evicted at capacity.
- Event and alert persistence uses the existing SQLite and local file watcher transaction model; there are no new SQL queries from untrusted input.
- The page is **static HTML** and inherits `script-src 'none'`, `connect-src 'none'`, `frame-ancestors 'none'`, `object-src 'none'`, HSTS, nosniff, X-Frame-Options, COOP/CORP and GET/HEAD-only dispatch. Legacy ARGUS page contains inline CSS and still requires its preexisting route-specific `style-src 'unsafe-inline'` exception.
- The ARGUS API remains an **unauthenticated loopback-only** read service by default. Do not override `--host` to a public interface without a separately reviewed authentication/access-control perimeter.
- No models, client-supplied telemetry, tokens, secrets or source databases are published to Cloudflare Pages.

## Residual risks and explicit limitations
1. `source` is treated as a distinct machine/host only when normalization supplies a trustworthy **host ID**. If it is an application/service identifier or shared alias, the multi-host inference may be false.
2. States live only inside the running Python process. Watch checkpoints survive restart, but multi-host state, deduplication windows and risk history are **not** rebuilt after restart. This is not exactly-once detection, a durable distributed correlator or a SIEM.
3. Bounded cardinality and time windows create evictions. Attackers who control log contents may cause evictions or artificially inflate counts using fresh IDs and spoofed sources; host/source integrity must be guaranteed by the trusted ingestion path. Event IDs are deduplicated only in the retained window, not globally.
4. Malicious timestamps, skew between hosts, benign shared egress IPs and overlapping existing rules can cause missed correlations or false positives. No host clocks are synchronized by the engine; out-of-order events are skipped.
5. The static page is **not** a live dashboard, has no websocket, API or hosted telemetry. Remaining legacy inline CSS and local API host override require separate work; this release deliberately minimizes changes to existing routes.
6. No external penetration test, fuzz campaign, production-scale memory measurement or independent field dataset validation is claimed. Results are illustrative and require human triage.

## Reproduction and release gates
From the The Workshop repository root:

```bash
python -m pip install -r argus/requirements.txt
python -m unittest discover -s argus/tests -v
python -m argus.main --config argus/config-v05-demo.yaml analyze \
  argus/samples/multihost_auth_v05.jsonl --db /tmp/argus-v05-demo.db
node --test web/workshop-labs/tests/*.test.mjs
```

- Python ARGUS regression workflow includes analyze/watch/stream resume and v0.4 Sigma smoke. Gate: **49 tests** expected at v0.5 (39 previous + 10 v0.5).
- Node Workshop Labs gate protects ARGUS content mirroring, historical navigation, NEXUS EXP-009, HeartAI, Blockchain and CERBERUS; default CSP and response headers must remain unchanged.
- Cloudflare Pages preview must be successful. Verify `/argus/`, `/nexus/`, `/nexus/exp009/`, `/heartai/`, `/crypto-lab/`, `/crypto-lab/pow/`, `/crypto-lab/signatures/` before production promotion.
- Deploy only from the GitHub `main` commit with successful gates and a preserved immutable rollback URL.

## Evidence
- GitHub CI, PR, preview and production identifiers: recorded in release conversation/PR after successful deployment. Do not interpret a passing unit test as an external penetration test.
