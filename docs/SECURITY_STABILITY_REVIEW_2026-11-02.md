# Security & Stability Review — 2026-11-02

Scope: public The Workshop / WolfPack web surfaces hosted on Cloudflare Pages and Workers.

Reviewed services:
- workshop-news.pages.dev
- workshop-labs.pages.dev
- wolfpack-crypto.pages.dev
- cerberus.wolfpackworkshop.workers.dev
- protocolo-ruby.wolfpackworkshop.workers.dev
- wolfpack.wolfpackworkshop.workers.dev
- workshop-kids.wolfpackworkshop.workers.dev
- workshop-security.wolfpackworkshop.workers.dev
- workshop-discord Worker configuration and source

## Executive status

Overall: **acceptable for a public research/education ecosystem, with several operational hardening items before treating the platform as business-critical.**

No reviewed source showed:
- arbitrary reverse proxying;
- shell or arbitrary server-side code execution;
- secrets committed into public source;
- permissive wildcard CORS on application APIs;
- browser-side collection of Workshop Kids chat history;
- unrestricted third-party scripts in the current Workshop News 2.0 homepage.

## Controls confirmed

### Workshop Kids
- Separate static/game/chat routes.
- Same-origin chat APIs with bounded JSON.
- Personal-data and high-risk content filters before AI.
- AI is optional, guarded on input/output and fails closed to curated responses.
- No application database for child conversations and no localStorage chat history.
- Route-specific CSP; static Blade comic has script/connect disabled.
- GitHub source tests and live smoke workflow are present and currently passing.

### Security Division
- D1 queries are parameterized.
- Flags are per-player/per-mission HMAC values derived from a Cloudflare secret.
- Session cookie uses Secure, HttpOnly and SameSite=Strict.
- Recovery and session hashes are stored instead of raw tokens.
- API responses are no-store; static assets use bounded caching.
- Request bodies and nickname/flag formats are bounded.
- Repeated flag attempts are rate-limited per player.
- CSP, frame denial, MIME-sniff prevention and restrictive permissions headers are present.

### Discord integration
- Interaction signatures are verified using Ed25519 against the raw request body.
- Signed timestamps are limited to a five-minute window.
- Commands are restricted to an explicit guild allowlist.
- No bot token is needed by the Worker.
- Inputs and outputs are bounded; mentions are disabled.
- AI path is optional, topic-limited, guarded, ephemeral and fail-closed.
- No Discord DM/message-history ingestion.

### WolfPack OS / Cerberus / Crypto Lab / Workshop Labs / News
- Mostly static or read-only surfaces.
- Explicit routes and deterministic 404/405 patterns are used in the reviewed Workers.
- WolfPack OS includes CSP hashes, HSTS and immutable asset/hash checks in CI.
- Cerberus is read-only and does not proxy arbitrary targets.
- Crypto Lab experiments are browser/local research content, not remote processing.
- Workshop News 2.0 currently loads no third-party script URL; the mascot redesign did not introduce an external JavaScript CDN.

## Findings

### HIGH — public interactive APIs lack account-wide abuse controls
Workshop Kids uses only an in-memory/per-instance limiter and Security Division limits submissions per player. These controls do not prevent distributed creation/restore/chat abuse or Workers AI cost amplification.

Recommendation:
- add Cloudflare Rate Limiting bindings or zone-level rules for interactive endpoints;
- separate limits for chat inference, session creation, restore and flag submission;
- return 429 with Retry-After;
- observe 429 volume and AI invocation rate.

### HIGH — production Pages are Direct Upload, not Git-integrated
Workshop News, Workshop Labs and WolfPack Crypto use manual/direct deployment. Production can diverge from Git history and CI, especially after visual hotfixes.

Recommendation:
- build an immutable deployment artifact from a commit;
- record commit SHA in every deployment;
- require source CI before production upload;
- retain at least one known-good rollback deployment;
- prefer Git integration or a controlled GitHub Actions deploy pipeline when practical.

### HIGH — Discord Worker is deployed but required configuration is not present in current Worker bindings
The deployed Worker currently exposes only the AI binding in inspected settings; required DISCORD_PUBLIC_KEY and ALLOWED_GUILD_IDS are not present. The source intentionally fails closed when these are missing, so this is primarily a readiness/availability issue.

Recommendation:
- configure DISCORD_PUBLIC_KEY and ALLOWED_GUILD_IDS before activating the Discord Interactions endpoint;
- keep ENABLE_AI false until moderation/budget review;
- confirm /health returns configured:true after setup.

### MEDIUM — public preview surfaces
The Worker workshop-kids-blade-preview had workers.dev enabled even though Blade is already integrated into the production Kids portal. It was disabled during this review.
Pages still has public preview deployments/aliases for visual experiments.

Recommendation:
- delete obsolete preview deployments or protect them with Cloudflare Access;
- never place secrets or unreleased private content in public preview builds.

### MEDIUM — Security Division anti-Sybil / account-creation abuse
The CTF deliberately has no CAPTCHA/Turnstile and no global creation rate limit. This is acceptable for a small beta but not for prizes or high-traffic public competition.

Recommendation:
- add Turnstile or a rate-limiter before competitive/public promotion;
- rate-limit /api/session and /api/restore independently from /api/submit;
- keep the leaderboard recreational until anti-Sybil controls exist.

### MEDIUM — observability is thin
Workers settings inspected during this review do not show a consistent logs/metrics strategy. Browser Rendering itself also hit rate limits while validating multiple sites, demonstrating why a single validation channel is insufficient.

Recommendation:
- enable Workers observability/logs for interactive Workers;
- add synthetic health checks for critical public routes;
- monitor 5xx, 429, latency, D1 errors and Workers AI failures;
- do not log child prompts, recovery tokens, Discord interaction tokens or CTF session secrets.

### MEDIUM — repository contains orphan gitlink entries
The main tree contains gitlink entries for "The Ouroboros Project " and "Wolfpack-Lair" while no readable .gitmodules file is present. GitHub Actions checkout emits cleanup warnings.

Recommendation:
- either restore a valid .gitmodules file with canonical repositories or remove the stale gitlinks;
- do not leave ambiguous submodule state in a release repository.

### LOW — Security Division header hardening
The Security Division already has a strong CSP and frame/MIME protections. Explicit HSTS and a stricter common security-header baseline should be added on the next Worker release for consistency with WolfPack/News.

## Changes applied during this review

1. Disabled public workers.dev access for workshop-kids-blade-preview.
2. Added .github/workflows/workshop-security.yml.
   - syntax checks;
   - reproducible build;
   - source tests;
   - placeholder/credential guard.
3. Added .github/workflows/workshop-discord.yml.
   - syntax checks;
   - Ed25519 / fail-closed tests;
   - credential guard.
4. Fixed the Discord CI credential-guard shell quoting after the first run exposed the workflow bug.
5. Confirmed final Security Division and Discord source gates pass.

## Release protocol recommended for every public site

1. Source and artifact tied to one Git commit.
2. Unit/security tests pass.
3. No secrets in artifact or logs.
4. CSP/security headers checked.
5. GET/HEAD/POST surface explicitly documented; unsupported methods deterministic.
6. 404/405/429/5xx must not be cached.
7. External URLs fixed/allowlisted; no arbitrary proxy target.
8. Interactive endpoints have body limits, abuse limits and fail-closed behavior.
9. Preview validated before production.
10. Production smoke checks critical routes and headers.
11. Rollback target recorded.
12. Release note records commit, deployment ID and residual risks.

**Decision:** continue public operation. Prioritize distributed rate limiting, Discord configuration, Direct Upload reproducibility and observability before scaling traffic.
