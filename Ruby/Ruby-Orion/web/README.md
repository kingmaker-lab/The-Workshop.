# 💎 Ruby Orion Studio v0.3 | Semi-Pro

**The Workshop Ruby Initiative · 4 interactive environments · CRuby 3.4 + WebAssembly**

Ruby Orion Studio is a browser-based Ruby engineering workbench focused on guided
practice, repeatable tests and **locally controlled execution**. No Ruby program is
executed on the Cloudflare Worker.

## Environments

| Environment | Capabilities |
|---|---|
| Ruby Playground | Ruby editor, STDIN/STDOUT/STDERR, pinned WASM runtime, timeout, cancellation, examples |
| Orion Labs | Eight executable labs, including five Semi-Pro challenges with explicit objectives and hints |
| Orion Test Bench | Multiple input/output cases per lab, independent Ruby VM per case, pass/fail report, duration, timeouts and locally stored progress |
| File Lab | Local file magic, entropy, SHA-256 and SHA-512 without server upload |

**Semi-Pro challenge series:** EXP-004 HTTP header audit; EXP-005 JSONL aggregation;
EXP-006 IPC frame validation; EXP-007 frequency index; EXP-008 SHA-256 integrity.

EXP-002 and EXP-003 in the browser demonstrate concepts and data structures.
Actual OS processes, UNIX pipes and native IPC remain limited to the local Orion CLI.

## Editor and privacy

- **Save** writes the current code to browser localStorage only on explicit click.
- **Load** restores a saved draft for the current lab or the scratch playground.
- **Import / export** use browser File and Blob APIs with no network transfer.
- Only completed lab IDs are automatically persisted to browser localStorage.
- Clearing site data removes local drafts and progress. No account, telemetry or cloud sync.

Never paste secrets or genuinely malicious code into the playground: Web Workers
and WebAssembly provide operational separation and termination, not a
security-grade sandbox. The external WASM module is pinned to the
`@ruby/wasm-wasi@2.10.1` and `@ruby/3.4-wasm-wasi@2.10.1` packages on jsDelivr.
Avoid relying on its CDN integrity or on browser-side tests for formal certification.

## Constraints and verification

- Source <= 8,000 chars; STDIN <= 4,000 chars per test.
- Test suite: 1 to 6 cases, each executed in a fresh WASM Ruby VM, 9s runtime
  timeout per case, 75s cold-start timeout.
- Result output is capped at 12 KiB per channel.
- Only local browser File Lab analysis (up to 8 MiB), using WebCrypto SHA digests.
- DOM output uses `textContent`; JavaScript's `eval` and `innerHTML` are not used.
- Strict CSP, no arbitrary server-side code execution; runtime Worker is disposable.

Test cases are shipped client-side to support education. They are **not
secret or tamper-resistant**, and completion records can be modified by the user.

## Local development and tests

```bash
cd Ruby/Ruby-Orion/web
ruby scripts/validate_site.rb
ruby scripts/build-worker.rb
node --check assets/studio.js
node --check assets/bench.js
node --check assets/ruby-worker.js
node --check dist/worker.mjs
python3 -m http.server 8080
```

In the browser, `/?selftest=1` checks Ruby runtime startup and
`/?benchtest=1` executes the EXP-001 suite, setting the hidden
`#bench-selftest` marker to `passed` on success.

CI currently runs the native CLI on **Linux / Ruby 3.3 and 3.4** and the
Studio validator on **Linux / Ruby 3.4**. Windows validation is pending:
the containing repository is named `The-Workshop.` (with a trailing dot),
which prevents GitHub Actions Windows from creating its checkout workspace.
Do not treat that omission as a Windows compatibility claim.

Reference solutions for the five intermediate challenges are under
`web/test/reference/` and are tested on native Ruby by CI. They are not
included in the public static-asset bundle.

## Deployment

Independent Cloudflare Worker:
https://orion.wolfpackworkshop.workers.dev/

The build tool generates `dist/worker.mjs`, a standalone static bundle.
GitHub pushes and merges do not deploy automatically. Deploy the verified
bundle manually with least-privilege authorization.

## Future hardening

- Self-host and integrity-pin the Ruby/WASM interpreter rather than depending
  on third-party CDN availability.
- Test multiple browser engines and lower-memory devices.
- Add optional local multi-file projects, error annotations and more robust
  diagnostics while keeping the native process supervisor private.

Reference: https://ruby.github.io/ruby.wasm/
