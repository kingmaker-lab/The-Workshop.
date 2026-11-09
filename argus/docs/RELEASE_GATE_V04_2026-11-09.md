# ARGUS v0.4 / Sigma subset — security & release gate

Date: 2026-11-09
Release scope: local-only Sigma-shaped rule evaluation integrated into the
existing ARGUS batch and stream engines, plus public static documentation.

## Specification baseline and feature boundary

Sigma specification reference:
https://github.com/SigmaHQ/sigma-specification/blob/main/specification/sigma-rules-specification.md

This implementation is not pySigma or a full Sigma translator. It accepts a
documented restricted grammar. Unknown data sources, fields, modifiers,
conditions and malformed files are rejected; nothing is interpreted as
Python code or a regular expression.

The only supported normalized logsource values use product `argus` and
category `authentication` or `network_connection`. Validation includes
a strict allowlist of field mappings, bounded selector lists, boolean
condition parser and deterministic case-insensitive string comparisons.
Unsupported wildcards, aliases, custom YAML tags and duplicate keys are
rejected. A positive match is required to prevent broad negative-only
detections. File count and size limits: 32 rules and 32 KiB each.

## Threat model

- Rule files are local, operator-supplied data. No remote download or HTTP
  rule upload. The public ARGUS page remains static (no scripts/form/API).
- New processing is disabled by default with `sigma.enabled: false`.
  The sample config explicitly enables only `argus/sigma/rules`.
- All rules are validated at startup before processing; bad rules fail closed.
  Existing deterministic rules continue to operate when Sigma is disabled.
- Imported Sigma rules from community repositories are **not guaranteed
  compatible**; direct import is rejected if the logsource or grammar does
  not match. Review rules and conduct test-event validation first.
- Additional Sigma findings contribute to the existing 0–100 risk score.
  False positives and overlapping findings with existing rules may increase
  aggregate severity. This does not mean an intrusion is confirmed.
- File system parents, file content mutation, large YAML parsing under the
  allowed 32 KiB bound, storage permissions and operational retention remain
  part of the trusted local operator boundary. No separate fuzzing campaign
  or external penetration test has been performed.
- API remains an unauthenticated loopback-only **read-only** HTTP service
  by default, and is NOT deployed to Cloudflare.

## Validation evidence

- ARGUS Python 3.12 CI: **PASS 39/39** unit/integration tests, covering
  exact/list selector semantics, boolean conditions, string modifiers,
  invalid fields/modifiers/values, malicious YAML constructs, file
  permissions/symlinks, logsource gates, opt-in and default-off behavior.
  CLI `sigma-validate` and sample opt-in analysis also PASS.
  https://github.com/kingmaker-lab/The-Workshop./actions/runs/42625275696
- Workshop Labs Node CI: **PASS 15/15**. Confirms source-to-Worker
  identical HTML, v0.3 and v0.4 documentation, static CSP,
  GET/HEAD/405 behavior and continued HeartAI support.
  https://github.com/kingmaker-lab/The-Workshop./actions/runs/42625355309

## Release decision

**LAB ONLY** for the Python Sigma subset. Public release permitted for
**documentation only**, after Cloudflare preview and production HTTP checks.
No remote rules, network collection, telemetry ingestion or public API.
Public deploy ID and post-deploy checks: to be appended after deployment.

## Preview verification

- Branch CI following CLI watch integration: **PASS**, 39/39 tests,
  opt-in Sigma analysis and `watch --once`, followed by resume at 0
  events: https://github.com/kingmaker-lab/The-Workshop./actions/runs/42625580346
- Workshop Labs CI: **PASS**, 15/15 tests:
  https://github.com/kingmaker-lab/The-Workshop./actions/runs/42625355309
- Cloudflare Pages preview `0e1e62a3-291c-4ec8-8e89-b90a8afd85de`
  (https://0e1e62a3.workshop-labs.pages.dev/argus/): **SUCCESS**.
- Browser Rendering of preview: HTTP 200, Sigma subsection and opt-in
  instructions present, ARGUS v0.3 and HeartAI navigation preserved.
- No tests involve sending real user telemetry to Cloudflare.

## Production release and post-deploy verification

- PR #34 merged to `main`: `10c1e4d0d0686b1d63d7c88029ba4d691c961546`.
- Cloudflare Pages production deployment:
  `14d23284-50b2-42a6-a48e-85237dfb5df6`,
  `https://14d23284.workshop-labs.pages.dev`:
  **production / deploy / success**.
- Live Browser Rendering of
  `https://workshop-labs.pages.dev/argus/`: **SUCCESS**;
  v0.4 Sigma, local validator, disabled-by-default disclosure, v0.3
  history and HeartAI link all present.
- Live Browser Rendering of `https://workshop-labs.pages.dev/heartai/`:
  **SUCCESS**; both BPE tokenizer and embeddings demos executed.
- Live Browser Rendering of `https://workshop-labs.pages.dev/`:
  **SUCCESS**; ARGUS, HeartAI, CERBERUS and Crypto Lab links retained.
- Post-merge GitHub Actions, all **SUCCESS**:
  - ARGUS regressions:
    https://github.com/kingmaker-lab/The-Workshop./actions/runs/42625949345
  - Workshop Labs:
    https://github.com/kingmaker-lab/The-Workshop./actions/runs/42625949326
  - immutable artifact gate:
    https://github.com/kingmaker-lab/The-Workshop./actions/runs/42625949313

Publication covers only static documentation. The Python Sigma engine
remains LAB ONLY, local and disabled unless explicitly opted in.
