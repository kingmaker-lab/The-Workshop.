import test from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { readFileSync } from "node:fs";

const buildPath = fileURLToPath(new URL("../build.mjs", import.meta.url));
execFileSync(process.execPath, [buildPath], { stdio: "pipe" });
const { default: worker } = await import("../dist/worker.mjs");
const domain = "https://workshop-store-preview.wolfpackworkshop.workers.dev";

async function probe(route, method = "GET") {
  return worker.fetch(new Request(domain + route, { method }));
}

test("rota raiz, JS e política privacidade são servidos em MIME correto", async () => {
  const expected = [
    ["/", "text/html; charset=utf-8"],
    ["/index.html", "text/html; charset=utf-8"],
    ["/privacidade", "text/html; charset=utf-8"],
    ["/privacidade.html", "text/html; charset=utf-8"],
    ["/app.js", "text/javascript; charset=utf-8"],
    ["/config.js", "text/javascript; charset=utf-8"],
    ["/styles.css", "text/css; charset=utf-8"]
  ];
  for (const [route, mime] of expected) {
    const res = await probe(route);
    assert.equal(res.status, 200, route);
    assert.equal(res.headers.get("content-type"), mime, route);
    assert.ok((await res.text()).length > 0, route);
  }
});

test("HTTP GET e HEAD funcionam, escrita é recusada", async () => {
  const get = await probe("/");
  const head = await probe("/", "HEAD");
  const post = await probe("/", "POST");
  assert.equal(get.status, 200);
  assert.equal(head.status, 200);
  assert.equal(await head.text(), "");
  assert.equal(post.status, 405);
  assert.equal(post.headers.get("allow"), "GET, HEAD");
});

test("rotas de protótipos JS e caminhos ausentes jamais passam pela allowlist", async () => {
  for (const route of ["/__proto__", "/constructor", "/toString", "/hasOwnProperty", "/not-found", "/.env", "/secrets", "/admin"]) {
    const res = await probe(route);
    assert.equal(res.status, 404, route);
    assert.equal(res.headers.get("cache-control"), "no-store");
  }
});

test("cabeçalhos defensivos, cache e preview sem indexação", async () => {
  const res = await probe("/");
  assert.equal(res.headers.get("cache-control"), "no-store");
  assert.match(res.headers.get("content-security-policy"), /frame-ancestors 'none'/);
  assert.match(res.headers.get("content-security-policy"), /script-src 'self'/);
  assert.equal(res.headers.get("x-content-type-options"), "nosniff");
  assert.equal(res.headers.get("x-frame-options"), "DENY");
  assert.equal(res.headers.get("referrer-policy"), "no-referrer");
  assert.equal(res.headers.get("cross-origin-opener-policy"), "same-origin");
  assert.equal(res.headers.get("cross-origin-resource-policy"), "same-origin");
  assert.equal(res.headers.get("x-robots-tag"), "noindex, nofollow, noarchive");
  const staticRes = await probe("/styles.css");
  assert.equal(staticRes.headers.get("cache-control"), "public, max-age=300");
});

test("o querystring não se reflete no HTML, sem HTML ou CSS inline", async () => {
  const attack = "<svg/onload=alert(1)>";
  const res = await probe("/?search=" + encodeURIComponent(attack));
  const body = await res.text();
  assert.equal(res.status, 200);
  assert.ok(!body.includes(attack));
  const privacy = readFileSync(fileURLToPath(new URL("../privacidade.html", import.meta.url)), "utf8");
  assert.ok(!/\sstyle\s*=/i.test(privacy));
  assert.ok(privacy.includes("Cloudflare"));
  assert.ok(privacy.includes("WhatsApp"));
});

test("a URL comercial de produção não recebe aviso de noindex", async () => {
  const res = await worker.fetch(new Request("https://workshop-store.wolfpackworkshop.workers.dev/"));
  assert.equal(res.status, 200);
  assert.equal(res.headers.get("x-robots-tag"), null);
});
