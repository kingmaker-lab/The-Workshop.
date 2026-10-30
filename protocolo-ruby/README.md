# 💎 Protocolo Ruby

Open-source static malware research for **The Workshop / Kingmaker Lab**.

## MVP v0.1

This experimental Ruby engine extracts hashes, header-format hints, ASCII strings, entropy and URL/IPv4 indicators. It never executes submitted files and does not produce malware/safety verdicts.

The complete initial working prototype, including a local web UI, CLI, tests and Apache-2.0 license, was assembled as a downloadable ZIP in the project conversation. The repository branch initially contains the core module and project documentation; web UI integration is next.

### Usage

```ruby
require_relative 'lib/protocolo_ruby/analyzer'
puts ProtocoloRuby::Analyzer.new.analyze(File.binread('sample.bin'))
```

Only analyze files you are authorized to handle. This version is for local experimentation, not public deployment. **Do not execute malware on the host.**