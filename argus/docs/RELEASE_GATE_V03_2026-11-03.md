# ARGUS v0.3 / Continuous local ingestion — security release gate

Date: 2026-11-03
Scope: `argus/stream/follower.py`, persistent SQLite checkpoints,
`argus.main watch`, tests and public static documentation.

## Threat model and boundaries

- Reads **operator-trusted local regular files** only. No HTTP ingest,
  remote log collection, network listeners, uploads or cloud processing.
- Use a non-root account with read-only access to logs and a private
  writable SQLite directory.
- The follower opens source files with `O_NOFOLLOW` and
  `O_NONBLOCK`, verifies `fstat` regular-file mode, and rejects
  symlinks, FIFOs and devices. Parent paths are still assumed trusted.
- Advisory `flock` serializes watchers per SQLite database.
- Complete newline-terminated lines only; default limits are 64 KiB
  per line, 200 lines per polling batch and 50,000 completed lines
  per process. Invalid complete records are skipped without logging
  their contents; oversized lines fail closed without checkpoint advance.
- Cursor advance, event and resulting alert are written in the **same
  SQLite transaction**. Deterministic event IDs include pathname,
  device, inode, source generation and byte offset. Checkpoint races
  fail closed.
- Explicit `watch` invocation required; batch `analyze` and existing
  local read-only API remain unchanged.

## Resilience and residual risks

- Missing files are retried on the next poll. Rename-based rotation
  and observed truncation reset the cursor and increment generation.
- A copytruncate followed by enough writes to refill the file between
  polls may not be detected. Lines written to an old inode after
  pathname rotation can be lost.
- Correlation windows, deduplication flags and Welford baselines are
  **in-memory only**: a restart preserves the committed cursor but
  does not reconstruct the detection state. This is NOT a guarantee
  of exactly-once **correlation effects**, or complete continuous
  intrusion detection coverage across process restarts.
- If a database write fails, the CLI exits rather than reusing mutated
  in-memory correlation state. Replaying the uncommitted line on
  restart may produce a different contextual alert.
- The process cap limits memory state growth in a single process,
  but very high source-cardinality logs, oversized field values up to
  per-line limit, disk pressure, malicious log producers, networked
  filesystems, path-parent symlinks, mutation in place, and OS access
  controls remain open hardening concerns.
- Checkpoints contain local absolute file paths; DB files and logs
  must be protected and retained under a clear privacy policy.
- No independent security audit, fuzzing campaign or performance
  stress test has been completed. **LAB ONLY**.

## Evidence

GitHub Actions Python 3.12 regression suite:
- `python -m unittest discover -s argus/tests -v`: **30/30 PASS**.
- CLI `analyze` synthetic sample: **17 records / 3 alerts**.
- CLI `watch --once`: **17 records / 3 alerts** after sample newline fix.
- CLI resume: **0 records / 0 alerts** on second invocation.
- Tests cover partial lines, restart resume, bounded processing,
  malformed/oversized records, network adaptation, hostile file types,
  rename rotation, observed truncation, writer lock, transactional
  checkpoint conflict and deterministic ID behavior.
- Evidence: https://github.com/kingmaker-lab/The-Workshop./actions/runs/41687317142

Workshop Labs static CI: **14/14 PASS**, including CSP and ARGUS v0.3
public page regressions:
https://github.com/kingmaker-lab/The-Workshop./actions/runs/41687523416

## Release decision

**LAB ONLY** for the Python watcher, with public publication approved only
for its **static documentation** on Workshop Labs after preview + live
HTTP and deployed Worker security checks. No live API, frontend-to-backend
connection, log uploads, elevated runtime or remote listener authorized.

Public production deployment and HTTP checks: pending at document creation.

## Public static preview verification

- Cloudflare Pages preview deployment:
  `16dbb09b-ed5e-4bb3-87fb-94d9c528a43e`,
  `https://16dbb09b.workshop-labs.pages.dev/argus/`: **SUCCESS**.
- Browser Rendering confirmed **HTTP 200**, v0.3 section, `watch`
  example, quotas, existing ARGUS architecture/roadmap and HeartAI
  link present.
- Workshop Labs CI for this code: **14/14 PASS**;
  https://github.com/kingmaker-lab/The-Workshop./actions/runs/41687570184
- ARGUS Python CI for release document revision: **PASS**;
  https://github.com/kingmaker-lab/The-Workshop./actions/runs/41687691197

Pending: production Cloudflare deployment and live smoke. No changes to
the local-only release restriction for the executable ARGUS engine.
