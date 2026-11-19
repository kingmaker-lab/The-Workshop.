import test from 'node:test';
import assert from 'node:assert/strict';
import worker from '../_worker.js';
const origin='https://workshop-labs.pages.dev/';
const fetchLocal=(path,method='GET')=>worker.fetch(new Request(new URL(path,origin),{method}));
test('Homepage cards include Blockchain while retaining labs',async()=>{
 const r=await fetchLocal('/'); assert.equal(r.status,200); const html=await r.text();
 for(const word of ['id="blockchain-experiments"','BLOCKCHAIN FUNDAMENTALS','PROOF-OF-WORK MINER','WALLETS &amp; DIGITAL SIGNATURES','CERBERUS PROTOCOL','NEXUS-06 NEURAL LAB','ARGUS PROJECT']){
  assert.ok(html.includes(word),word);
 }
 assert.ok(html.includes('href="#blockchain-experiments"'));
});
test('Blockchain EXP-001 through EXP-003 and assets',async()=>{
 for(const [path,needle] of [
  ['/crypto-lab/','Blockchain, por dentro'],
  ['/crypto-lab/pow/','Proof-of-Work'],
  ['/crypto-lab/signatures/','Assinaturas Digitais'],
  ['/crypto-lab/app.js','crypto.subtle.digest'],
  ['/crypto-lab/pow/miner.worker.js','SHA-256'],
  ['/crypto-lab/signatures/protocol.js','ECDSA'],
 ]){
  const r=await fetchLocal(path); assert.equal(r.status,200,path);
  assert.ok((await r.text()).includes(needle),path+' '+needle);
  const h=await fetchLocal(path,'HEAD'); assert.equal(h.status,200,path+' HEAD'); assert.equal(await h.text(),'');
 }
});
test('Unknown and unsafe methods denied',async()=>{
 assert.equal((await fetchLocal('/crypto-lab/nope')).status,404);
 assert.equal((await fetchLocal('/crypto-lab/','POST')).status,405);
});
test('Core labs survive',async()=>{
 for(const p of ['/','/argus/','/heartai/','/nexus/','/assets/labs.css']){
  assert.equal((await fetchLocal(p)).status,200,p);
 }
});
