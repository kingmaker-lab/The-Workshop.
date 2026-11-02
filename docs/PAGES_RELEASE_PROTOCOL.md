# Pages Release Protocol

Applies to Workshop News, Workshop Labs and WolfPack Crypto Lab.

The public sites remain Direct Upload projects. This protocol makes Direct Upload reproducible without changing their application structure.

## Flow

1. Commit source to Git.
2. Run project tests.
3. Build one immutable artifact from that commit.
4. Record SHA-256 in `release-manifest.json`.
5. Upload the artifact as a GitHub Actions artifact.
6. Manual promotion downloads that exact artifact by run ID + commit SHA.
7. Deploy it to a Pages preview branch.
8. Smoke-test the preview.
9. Promote the same bytes to `main`.
10. Smoke-test production.
11. Record commit, preview and rollback evidence in the workflow summary.

No production rebuild happens between preview and production.

## Required repository secrets for promotion

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`

The token should have only the minimum Pages deployment permission needed for these projects.

## Rollback

Cloudflare Pages retains previous deployments. If production smoke fails, promote the previous successful deployment. The release summary records the commit being promoted so the rollback target can be identified deterministically.

## Source mapping

- Workshop News 2.0: `sites/workshop-news/` (Worker + current static assets)
- Workshop Labs: `web/workshop-labs/_worker.js`
- WolfPack Crypto: `sites/wolfpack-crypto/worker.mjs`

The builder copies each declared source file byte-for-byte into the deployment directory, records a SHA-256 for every file plus an aggregate manifest hash, and does not minify, bundle, rewrite, or modify runtime behavior.
