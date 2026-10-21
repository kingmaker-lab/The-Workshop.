// Post-deploy smoke checks. Requires Node.js 20+.
import assert from "node:assert/strict";

const base = process.env.CERBERUS_BASE_URL || "https://cerberus.wolfpackworkshop.workers.dev";
async function fetchPage(path, init={}) {
  const res = await fetch(new URL(path,base), {signal:AbortSignal.timeout(15000),...init});
  const body = (init.method==="HEAD") ? "" : await res.text();
  return {res,body};
}
const {res:home,body:index} = await fetchPage("/");
assert.equal(home.status,200);
assert.ok(index.includes('href="/labs/01"'));
assert.ok(index.includes('href="/labs/02"'));
assert.ok(index.includes("CERBERUS_02"));
assert.ok(home.headers.get("content-security-policy")?.includes("script-src 'none'"));
assert.equal(home.headers.get("x-content-type-options"),"nosniff");
assert.equal(home.headers.get("x-frame-options"),"DENY");
console.log("PASS home, both cards and safety headers");

const {res:first,body:firstHtml}=await fetchPage("/labs/01");
assert.equal(first.status,200);
assert.ok(firstHtml.includes("monólito modular"));
const {res:second,body:secondHtml}=await fetchPage("/labs/02");
assert.equal(second.status,200);
for(const word of ["Hexagonal","InMemoryReservations","SQLiteReservations","ADR-0002"]) {
  assert.ok(secondHtml.includes(word),word);
}
assert.equal((await fetchPage("/labs/02/")).res.status,200);
console.log("PASS experiments 01 and 02");

const {res:status,body:statusRaw}=await fetchPage("/api/status");
assert.equal(status.status,200);
const state=JSON.parse(statusRaw);
assert.equal(state.version,"0.3.0");
assert.equal(state.available_labs,2);
const {res:modules,body:modRaw}=await fetchPage("/api/modules");
assert.equal(modules.status,200);
const item=JSON.parse(modRaw).modules.find(p=>p.id==="cerberus-02");
assert.equal(item.status,"available");assert.equal(item.route,"/labs/02");
assert.equal((await fetchPage("/api/projects")).res.status,200);
assert.equal((await fetchPage("/labs/02",{method:"HEAD"})).res.status,200);
assert.equal((await fetchPage("/.env")).res.status,404);
assert.equal((await fetchPage("/",{method:"POST"})).res.status,405);
console.log("PASS registry, backward compatibility, 404, HEAD, 405");
console.log("CERBERUS_02 production smoke PASSED");
