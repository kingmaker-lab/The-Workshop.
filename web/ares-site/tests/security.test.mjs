import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {fileURLToPath} from "node:url";

const code = readFileSync(fileURLToPath(new URL("../_worker.js", import.meta.url)), "utf8");
const moduleURL = "data:text/javascript;base64," + Buffer.from(code, "utf8").toString("base64");
const {default: worker} = await import(moduleURL);
const origin = "https://workshop-labs.pages.dev";

function request(path, method = "GET") {
  return worker.fetch(new Request(origin + path, {method, redirect:"manual"}));
}
function assertHeaders(response) {
  assert.equal(response.headers.get("x-content-type-options"), "nosniff");
  assert.equal(response.headers.get("x-frame-options"), "DENY");
  assert.equal(response.headers.get("referrer-policy"), "no-referrer");
  assert.equal(response.headers.get("cross-origin-opener-policy"), "same-origin");
  assert.equal(response.headers.get("cross-origin-resource-policy"), "same-origin");
  assert.match(response.headers.get("strict-transport-security"), /max-age=31536000/);
  const csp = response.headers.get("content-security-policy");
  assert.match(csp, /default-src 'none'/);
  assert.match(csp, /frame-ancestors 'none'/);
  assert.match(csp, /script-src 'self'/);
  assert.doesNotMatch(csp, /script-src[^;]*'unsafe-inline'/);
  assert.doesNotMatch(csp, /script-src[^;]*'unsafe-eval'/);
}

test("home and all ARES labs serve HTML with defense headers", async () => {
  const paths = [
    "/", "/projects/ares/", "/projects/ares/tcp-foundation/",
    "/projects/ares/http-parser/", "/projects/ares/responses-routing/"
  ];
  for (const path of paths) {
    const r = await request(path);
    assert.equal(r.status, 200, path);
    assert.match(r.headers.get("content-type"), /^text\/html/);
    assertHeaders(r);
    const html = await r.text();
    assert.ok(html.startsWith("<!doctype html>"), path);
    assert.doesNotMatch(html, /<script(?=\s|>)[^>]*\s(?:src=)?https?:\/\//i, path);
    const externalLinks = html.match(/<a\b[^>]*target="_blank"[^>]*>/g) || [];
    for (const link of externalLinks) {
      assert.match(link, /rel="[^"]*noopener/);
      assert.match(link, /rel="[^"]*noreferrer/);
    }
  }
});

test("HEAD responses don't send bodies", async () => {
  for (const path of ["/", "/projects/ares/", "/projects/ares/responses-routing/",
                      "/assets/ares.css", "/favicon.svg"]) {
    const r = await request(path, "HEAD");
    assert.equal(r.status, 200);
    assert.equal(await r.text(), "");
    assertHeaders(r);
  }
});

test("assets use correct content types and defensive headers", async () => {
  const assets = {
    "/assets/ares.css": "text/css",
    "/assets/hub.css": "text/css",
    "/assets/tcp.css": "text/css",
    "/assets/http-parser.css": "text/css",
    "/assets/ares.js": "application/javascript",
    "/favicon.svg": "image/svg+xml"
  };
  for (const [path, mime] of Object.entries(assets)) {
    const r = await request(path);
    assert.equal(r.status, 200, path);
    assert.ok(r.headers.get("content-type").startsWith(mime));
    assertHeaders(r);
  }
});

test("unexpected HTTP methods are rejected and not echoed", async () => {
  for (const method of ["POST", "PUT", "DELETE", "PATCH"]) {
    const r = await request("/projects/ares/", method);
    assert.equal(r.status, 405, method);
    assert.equal(r.headers.get("allow"), "GET, HEAD");
    assert.equal(await r.text(), "405 Method Not Allowed");
    assertHeaders(r);
  }
});

test("unknown and sensitive paths return uniform, non-reflective 404", async () => {
  for (const path of ["/.env", "/_worker.js", "/admin", "/projects/ares/%3Cscript%3E"]) {
    const r = await request(path);
    assert.equal(r.status, 404, path);
    assert.equal(await r.text(), "404 — Not Found");
    assertHeaders(r);
  }
  const xss = "<script>alert(1)</script>";
  const r = await request("/?message=" + encodeURIComponent(xss));
  assert.equal(r.status, 200);
  assert.ok(!(await r.text()).includes(xss), "reflected query in HTML");
});

test("Crypto Labs redirect uses fixed trusted target", async () => {
  for (const path of ["/projects/crypto/", "/crypto/", "/crypto-labs/"]) {
    const r = await request(path);
    assert.equal(r.status, 302);
    assert.equal(r.headers.get("location"), "https://wolfpack-crypto.pages.dev/");
    assertHeaders(r);
  }
});

test("no secrets or dynamic script execution patterns in Worker source", () => {
  assert.doesNotMatch(code, /eval\s*\(/);
  assert.doesNotMatch(code, /new\s+Function\s*\(/);
  assert.doesNotMatch(code, /api[_-]?token\s*[:=]/i);
  assert.doesNotMatch(code, /private[_-]?key\s*[:=]/i);
});
