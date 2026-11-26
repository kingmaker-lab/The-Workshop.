# The Workshop | Mobile Division

**Pulse · DECONSTRUCTION · Explore. Deconstruct. Rebuild.**

## EXP-001 — Anatomy of an APK

Status: implementation and test cases committed; execution pending verification.

Hypothesis: a standard-library-only Python inspector can inventory APK ZIP metadata without executing or extracting the payload.

### Reproduce locally

Requires Python 3.10+; no external dependencies.

```bash
cd mobile-division
python3 -m unittest discover -s tests -v
python3 tools/pulse_inspector.py /path/to/owned-app.apk
```

The tests generate synthetic ZIP fixtures with APK-like names. They are intentionally not installable APKs and do not contain valid DEX, ELF or signatures. A real, locally built Android application is the next validation dataset.

### Protocol

- Compare SHA-256 with an independent local hash.
- Compare entry count, manifest presence, DEX names, library ABI names and v1 signature artifact names against the fixture ground truth.
- Reject traversal-like paths, duplicate entries, symlinks, encrypted entries and oversized archives or suspicious declared ratios.
- Record actual test output and environment before declaring the hypothesis supported.

### Limits

64 MiB input, 4096 entries, 64 MiB declared member size, 256 MiB declared expanded total, maximum declared compression ratio 200:1. Legitimate archives can exceed these conservative bounds. The standard ZIP parser reads the central directory before the entry-count check; limits are not a substitute for process isolation. Use trusted local file paths, read-only inputs and an isolated process for untrusted samples. No network upload, execution or extraction.

This is a metadata inventory, not an APK validity checker, malware detector or signature verifier. Names and declared sizes are untrusted metadata. Binary manifest decoding, DEX/ELF validation, APK v2/v3/v4 signature verification, Android SDK comparisons and performance measurements are not implemented.

### Roadmap

EXP-002: binary AndroidManifest and permissions.
EXP-003: DEX structures.
EXP-004: native ELF and JNI.
EXP-005: signature and integrity checks.
EXP-006: runtime experiments on owned applications and isolated emulators.
