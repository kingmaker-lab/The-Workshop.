import assert from "node:assert/strict";
import worker from "./worker.mjs";

const origin = "https://wolfpack-crypto.pages.dev";
async function get(path, init = {}) {
  return worker.fetch(new Request(origin + path, init));
}

const oldRoutes = [
  "/", "/experimentos/", "/experimentos/001/", "/experimentos/002/",
  "/experimentos/003/", "/experimentos/004/", "/experimentos/005/",
  "/experimentos/006/", "/experimentos/007/", "/experimentos/009/",
  "/assets/style.css", "/assets/site.js",
];
for (const path of oldRoutes) {
  const response = await get(path);
  assert.equal(response.status, 200, `legacy route failed: ${path}`);
}

const newRoutes = [
  ["/experimentos/010/", "Multi-round Feistel Trail Analysis"],
  ["/experimentos/011/", "Multi-round Differential Trails"],
  ["/experimentos/012/", "KS1 Key Schedule Analysis"],
  ["/experimentos/013/", "Related-Key Dependency"],
  ["/experimentos/014/", "Research Consolidation"],
];
for (const [path, expected] of newRoutes) {
  const response = await get(path);
  assert.equal(response.status, 200, `new route failed: ${path}`);
  const html = await response.text();
  assert.ok(html.includes(expected), `expected page title missing: ${path}`);
  assert.ok(html.includes("Pesquisa experimental, não uma cifra validada"));
}

const home = await (await get("/")).text();
assert.ok(home.includes("Explorar 14 experimentos"));
assert.ok(home.includes("latest-exp-010-014"));
assert.ok(home.includes("Ouroboros Low Level"));
assert.ok(home.includes("Hash Playground"));
const archive = await (await get("/experimentos/")).text();
for (const [path] of newRoutes) assert.ok(archive.includes(path));
assert.ok(archive.includes("EXP / 009"));

const gridStart = archive.indexOf('<div class="experiment-grid">');
const gridEnd = archive.indexOf('</div><section class="section" id="research-007">', gridStart);
assert.ok(gridStart >= 0 && gridEnd > gridStart, "experiment archive grid boundary missing");
const gridHtml = archive.slice(gridStart, gridEnd);
let cursor = 0;
let articleDepth = 0;
let articleCount = 0;
while (cursor < gridHtml.length) {
  const openAt = gridHtml.indexOf("<article", cursor);
  const closeAt = gridHtml.indexOf("</article>", cursor);
  if (openAt < 0 && closeAt < 0) break;
  if (openAt >= 0 && (closeAt < 0 || openAt < closeAt)) {
    assert.equal(articleDepth, 0, "each experiment card must be a direct grid child");
    articleDepth += 1;
    articleCount += 1;
    cursor = openAt + "<article".length;
  } else {
    articleDepth -= 1;
    assert.equal(articleDepth, 0, "experiment cards must not be nested");
    cursor = closeAt + "</article>".length;
  }
}
assert.equal(articleDepth, 0, "all experiment cards must be closed");
assert.equal(articleCount, 14, "archive must render fourteen sibling cards");

const stylesheet = await (await get("/assets/style.css")).text();
assert.ok(stylesheet.includes(".experiment-grid{grid-template-columns:repeat(2"), "desktop/tablet experiment grid layout missing");
assert.ok(stylesheet.includes("@media(max-width:620px){.experiment-grid{grid-template-columns:1fr}"), "mobile single-column experiment layout missing");

const extensionless = await get("/experimentos/014");
assert.equal(extensionless.status, 200);
const css = await get("/assets/style.css");
assert.match(css.headers.get("content-type"), /text\/css/);
const js = await get("/assets/site.js");
assert.match(js.headers.get("content-type"), /javascript/);
const post = await get("/", { method: "POST" });
assert.equal(post.status, 405);
const missing = await get("/experimentos/099/");
assert.equal(missing.status, 404);

console.log("WolfPack Crypto Lab smoke tests passed: legacy routes, EXP-010–014, assets, navigation, 404 and method policy.");
