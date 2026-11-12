# 💎 Protocolo Ruby · v0.4 Browser Alpha / Ruby Staging
**The Workshop / Kingmaker Lab · MVP v0.1**

Open-source static malware analysis in Ruby, with browser UI, CLI and JSON API. It does not execute samples or claim a file is safe or malicious.

## Start locally
Requires Ruby 3.3+, minitest and WEBrick (`gem install webrick` if necessary).

```bash
cd protocolo-ruby
ruby test/analyzer_test.rb
ruby web/server.rb
# Open http://127.0.0.1:9292
```

CLI: `ruby bin/analyze path/to/file.bin`.

## Features
SHA-256/SHA-1/MD5; PE/ELF/PDF/ZIP header hints; Shannon entropy; printable ASCII strings; URL and IPv4 indicators; JSON report.

## API
`POST /api/analyze` with raw binary body, `Content-Type: application/octet-stream` and optional `X-Filename`. Maximum 20 MiB. Uploaded files are processed in memory and not intentionally persisted.

## Security
**Local development only. Never publish WEBrick directly to the Internet.** No authentication, worker sandboxing or malware-resistant parsing is available in v0.1. Treat all uploads and reports as untrusted. Detection is heuristic and deliberately returns `indeterminate`.

## Roadmap
v0.2 verified PE/ELF parsing and YARA-X; v0.3 Rails authentication and queued workers; later isolated VM behavioral analysis and intel correlation.

## Licensing
Apache License 2.0; complete license text is included in the downloadable release ZIP. See https://www.apache.org/licenses/LICENSE-2.0.

## v0.4 additions (November 2026)

- Basic, bounded PE (COFF machine, declared section count, PE32/PE32+ optional-header marker) and ELF (32/64-bit class, endianness, e_type and e_machine) header inspection.
- First 128 bytes in hexadecimal for triage. This is a preview, not a full hex editor.
- Explainable informational hints for high entropy, extracted URL strings and truncated executable headers. Findings never determine maliciousness.
- Browser-only implementation on Cloudflare and corresponding Ruby engine on Render staging; no real sample upload to the Ruby backend.
- Cloudflare's deployed Worker is version-controlled in `cloudflare/worker.js`.

**Limits:** PE/ELF checks are partial header inspection, not validation of full executable structure. The live frontend uses JavaScript; Ruby analysis is available only through a synthetic fixture demo on Render. Additional tests were performed locally for the inspector, but browser and cloud end-to-end behavior has not been independently verified.
