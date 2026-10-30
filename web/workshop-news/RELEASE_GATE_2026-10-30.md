# Workshop News: ARGUS v0.2 publication gate (2026-10-30)

## Change

This release adds a static `/argus/` story and inserts an ARGUS card on
the news homepage. All other paths continue using the known-good Pages
deployment `aae8ce82.workshop-news.pages.dev` as a pinned upstream.

This approach is **transitional**: the original Workshop News code and
asset manifest are not yet stored in this repository. The fixed upstream
prevents unintended loss of news feeds, styles, JavaScript, and redirects.

## Evidence

- Node 22 test run, **PASS**:
  https://github.com/kingmaker-lab/The-Workshop./actions/runs/41096235710
- Cloudflare Pages preview deployment, **SUCCESS**:
  https://406cfb8d.workshop-news.pages.dev/
- Browser Rendering of preview homepage: **HTTP 200**; the original
  NEWSROOM and "Da bancada" content is present; `/argus/` link is present.
- Browser Rendering of preview article: **HTTP 200**; ARGUS v0.2,
  test evidence and uncertainty caveat present.
- No secrets or private telemetry in published HTML.
- All external fetch destinations are fixed; incoming query/path cannot
  change upstream hostname. Authorization and cookies are not forwarded.

## Residual risks

- The pinned old deployment could be deleted or become unavailable,
  causing 502 errors on the original news content.
- Each proxied page adds an extra internal fetch; latency and service
  dependency remain until the original site assets and source are migrated
  to the repository and deployed directly.
- Scripted news feeds and dynamic endpoints need periodic functional
  verification; tested pages confirm markup, not every external feed.
- Browser rendering checks have not measured page performance, CLS or
  screen-reader accessibility.

## Decision

**CONDITIONAL PUBLICATION**: publish if CI remains green and the preview
passes external HTTP validation. Keep the old deployment and its URL
untouched and document the dependency. Before any long-term release,
replace the pinned upstream with a fully versioned, self-contained
Workshop News Pages build.

Review: ChatGPT-assisted implementation; human review recommended.

## Production verification — 2026-10-30

- New Pages production deployment: `0318d9e0-d450-4256-835e-8a1724f7895a`, **SUCCESS**.
- Live home `https://workshop-news.pages.dev/`: **HTTP 200** in Browser Rendering;
  original NEWSROOM and "Da bancada" content retained, new `/argus/` link present.
- Article `/argus/`: **HTTP 200 in preview**, expected ARGUS v0.2,
  references and risk statement present.
- Subsequent live article check: **NOT VERIFIED** (Cloudflare Browser
  Rendering rate limit). Deployment status is not a substitute for a live
  route response; recheck is recommended.
- Security and status checks: original content remains dependent on the pinned
  previous deployment and must not be deleted until source migration.
