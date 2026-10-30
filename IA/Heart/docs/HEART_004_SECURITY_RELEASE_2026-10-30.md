# HeartAI HEART_004 — Security & Release Gate (2026-10-30)

## Scope
- Python-only local `TokenEmbeddings`: seeded input/context matrices, bounded
  skip-gram negative-sampling, vector pooling and cosine similarity.
- Small, independent browser embedding research demo from a **fixed public**
  corpus; no inference services or user data stored or uploaded.
- Existing Byte-BPE Tokenizer Playground and independent ARGUS project retained.

## Threat model and limits
- Untrusted numeric tokens and lengths are validated. Python training limits:
  259..4096 vocabulary entries, 2..128 dimensions, 1000 sequences,
  15000 total training tokens, 60000 context pairs, and 2 million
  element-updates (estimated) per fit.
- No model inference API, no process execution, no user-provided URL,
  no shell commands, and no public stateful backend.
- Browser routes serve only local first-party JS; `script-src 'self'`,
  `connect-src 'none'`, `frame-ancestors 'none'`, `nosniff`, GET/HEAD only.
- All user-visible output goes through `textContent`, avoiding HTML reflection.
- Browser training is a toy fixed-corpus example, not the Python model.
  The output is **not** reliable semantic similarity. False confidence,
  domain shifts and poor training data are known methodological limitations.

## Evidence and release decision
- HeartAI full Python regression: **PASS**, 36 tests, Python 3.11, plus CLI
  demo smoke: https://github.com/kingmaker-lab/The-Workshop./actions/runs/41099124700
- Workshop Labs Node security regression: **PASS**, 10 tests:
  https://github.com/kingmaker-lab/The-Workshop./actions/runs/41099294181
- Code review: local-only, first-party routes and bounded input.
- Browser preview/live verification: PENDING at creation of this record.
- Load testing and external penetration testing: NOT VERIFIED.
- Decision: **CONDITIONAL PUBLICATION**, static demo only. No public
  HeartAI backend, private data ingestion or network inference approved.

The security review applies to this static demonstration and does not certify
the experimental vectors as accurate or safe to use for decisions.
