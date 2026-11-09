// node --test web/crypto-lab/pow/tests/pow.test.cjs
// Exercises the real browser Web Worker with Node's Web Crypto API; no extra dependencies.
const test = require("node:test");
const assert = require("node:assert/strict");
const {webcrypto,createHash} = require("node:crypto");
const {readFileSync} = require("node:fs");
const {resolve} = require("node:path");
const vm = require("node:vm");
const code = readFileSync(resolve(__dirname, "../miner.worker.js"), "utf8");
const ZERO = "0".repeat(64);

async function mine(data) {
  const messages = [];
  const self = {postMessage(msg) { messages.push(msg); }};
  const context = {self, crypto:webcrypto, TextEncoder, performance};
  vm.runInNewContext(code, context);
  await self.onmessage({data:{type:"mine", ...data}});
  return messages;
}
function canonical(b) {return JSON.stringify([b.index,b.previousHash,b.data,b.difficulty,b.nonce]);}
function digest(s) {return createHash("sha256").update(s).digest("hex");}
test("EXP-002: proof-of-work at difficulty 1 and 2", async () => {
  for (const difficulty of [1,2]) {
    const output = await mine({index:1,previousHash:ZERO,data:"The Workshop",difficulty});
    const found = output.find(x=>x.type==="found");
    assert.ok(found, "Miner should find a nonce");
    const b = found.block;
    assert.equal(b.hash,digest(canonical(b)));
    assert.equal(b.hash.startsWith("0".repeat(difficulty)),true);
    assert.equal(b.nonce+1,found.attempts);
    assert.ok(found.attempts <= 500000);
  }
});
test("EXP-002: linked second block and independent verification", async () => {
  const first=(await mine({index:1,previousHash:ZERO,data:"first",difficulty:2})).find(x=>x.type==="found").block;
  const second=(await mine({index:2,previousHash:first.hash,data:"second",difficulty:2})).find(x=>x.type==="found").block;
  assert.equal(second.previousHash, first.hash);
  assert.equal(second.hash,digest(canonical(second)));
  assert.ok(second.hash.startsWith("00"));
});
test("EXP-002: tampering changes the digest", async () => {
  const original=(await mine({index:1,previousHash:ZERO,data:"original",difficulty:1})).find(x=>x.type==="found").block;
  const tampered={...original,data:"modified"};
  assert.notEqual(digest(canonical(tampered)),original.hash);
});
test("EXP-002: invalid difficulty or previous hash rejected", async () => {
  for(const x of [{index:1,previousHash:ZERO,data:"x",difficulty:9},{index:1,previousHash:"invalid",data:"x",difficulty:1}]) {
    const messages=await mine(x);
    assert.equal(messages.length,1);
    assert.equal(messages[0].type,"error");
  }
});
