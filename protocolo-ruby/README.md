# 💎 Protocolo Ruby
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
