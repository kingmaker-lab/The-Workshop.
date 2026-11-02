# Pages rollback baseline — 2026-11-02

Baseline captured before switching future releases to the immutable artifact promotion workflow.

| Project | Current successful production | Immediate successful rollback |
| --- | --- | --- |
| workshop-news | `7a942297-41e3-4db7-a2c8-78ac83b8aa44` | `a77b8b81-17a7-4911-8f17-16437d42e111` |
| workshop-labs | `7e07493d-6fad-4724-8808-06641d15d058` | `47d8249e-fed2-42cd-a999-fb01568e9dc7` |
| wolfpack-crypto | `647b3b38-a68e-4a66-a693-098edaa40972` | `d5bf2b1b-0bca-47c8-98ac-37c23b5cfa2a` |

No production deployment was changed while creating this baseline.

Future releases should use `.github/workflows/pages-artifact-gate.yml` followed by `.github/workflows/pages-promote.yml` so preview and production consume the same immutable bytes.
