import test from "node:test";
import assert from "node:assert/strict";
import worker, { cardRoutes } from "./worker.js";

function fakeElement(tagName = "article") {
  const attrs = new Map();
  return {
    tagName, attrs, content: null, appended: "",
    setAttribute(k,v) { attrs.set(k,v); },
    setInnerContent(v) { this.content=v; },
    append(v) { this.appended+=v; },
  };
}
class Rewriter {
  constructor() { this.handlers = new Map(); globalThis.capturedRewriter = this; }
  on(selector, handler) { this.handlers.set(selector, handler); return this; }
  transform(res) { return res; }
}
globalThis.HTMLRewriter = Rewriter;

const html = new Response("<!doctype html><html><style id='wolfpack-critical-css'></style><body>asset</body></html>", {
  headers: {"content-type": "text/html; charset=utf-8", etag: '"before"', "content-length": "128"},
});
function environment() {
  const paths=[];
  return { paths, env: {ASSETS: {fetch: async r => { paths.push(new URL(r.url).pathname); return html.clone(); }}} };
}
test("card URLs are HTTPS and match published labs", () => {
  assert.deepEqual(Object.values(cardRoutes), [
    "https://workshop-labs.pages.dev/projects/ares/",
    "https://cerberus.wolfpackworkshop.workers.dev/",
  ]);
});
test("rewrites only homepage, preserving assets and downloads", async() => {
  const {paths,env}=environment();
  const download = await worker.fetch(new Request("https://wolfpack.wolfpackworkshop.workers.dev/downloads/raven-ruby-v0.1-original.zip"),env);
  assert.equal(await download.text(),await html.clone().text());
  assert.deepEqual(paths,["/downloads/raven-ruby-v0.1-original.zip"]);
  const home = await worker.fetch(new Request("https://wolfpack.wolfpackworkshop.workers.dev/"),env);
  assert.equal(home.headers.get("etag"),null);
  assert.equal(home.headers.get("cache-control"),"public, max-age=60, s-maxage=60");
});
test("card handlers create anchors without JavaScript redirects", async() => {
  const {env}=environment();
  await worker.fetch(new Request("https://wolfpack.wolfpackworkshop.workers.dev/"),env);
  const handlers=globalThis.capturedRewriter.handlers;
  const a=fakeElement(),c=fakeElement();
  handlers.get(".app-grid > article.app-card:nth-child(3)").element(a);
  handlers.get(".app-grid > article.app-card:nth-child(6)").element(c);
  for(const [el,url] of [[a,cardRoutes.ares],[c,cardRoutes.cerberus]]) {
    assert.equal(el.tagName,"a");assert.equal(el.attrs.get("href"),url);
    assert.equal(el.attrs.get("rel"),"noopener noreferrer");
    assert.equal(el.attrs.get("referrerpolicy"),"no-referrer");
    assert.ok(el.attrs.get("aria-label"));
  }
  assert.ok(handlers.has(".app-grid > article.app-card:nth-child(6) .app-card-body p"));
  assert.ok(handlers.has(".app-grid > article.app-card:nth-child(6) .app-card-bottom .app-muted"));
});
