# Render staging backend (Ruby)

This service is a Ruby API **staging proof**, not public malware ingestion. It serves only:
- `GET /health` (health status)
- `GET /v1/capabilities` (available features)
- `GET /v1/demo` (hardcoded harmless fixture analyzed with the real Ruby engine)

All non-GET requests, including file uploads, return HTTP 405. All other paths return 404. No Redis/Sidekiq or YARA-X job execution is enabled. Never pass the public API a malware sample.

For Render native Ruby runtime, deploy repository branch `feature/protocolo-ruby-v0.1`, with build command `cd protocolo-ruby/render && bundle install`, and start command `cd protocolo-ruby/render && bundle exec ruby server.rb`. Use Free tier and autoDeploy disabled until verified. `PORT` is provided by Render.

Next: integrate a secured queue service and authorization/limits *before* any uploads are enabled.
