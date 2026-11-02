import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import worker from './worker.mjs';

const root='https://wolfpack.wolfpackworkshop.workers.dev';
const fixtures={
"/index.html":["6127b92831972c8a8726ce0a1c57a346899ed80ac361a919b83ba996368940f5",134244],
"/js/ruby-worker.js":["325c63f24f6fd69090794b72af164c56c1f2b46c2df12dfd4a0b711ae23e67d3",3858],
"/downloads/raven-ruby-v0.1-original.zip":["ab3afe7a51cbf62fd1e2a5ff8a17797e00678370f4070e843afb032ecb5a82ac",8795],
"/downloads/vulpes77-terminal-v0.1-original.zip":["106738b06d7adda787ad3526f0fc1fb3b53aeeaf783c93da8cdbbad179acf245",13045],
"/downloads/wolfpack-ruby-protocol-v0.1.zip":["7d41e5747111cc1159cd947e8613d16893b042b9bd36bd1d3e2dc89fbfe3c054",16274],
"/cerberus-gatekeeper.html":["027938d880ef2a884172a0be3586c02d0ebeb9319c88218454d38ddf39388a2a",11312],
"/logic-forge.html":["694689796fb662084e84bd25e4d6392d04020f1dcae1b10bbee39a7d1633ab7a",3358],
"/logic-forge.css":["2efbf0e1559abc7f891f6a03a04836d7067fe8dd5a69998cd2bd12f194e68b71",6424],
"/logic-forge.js":["e1c06f227dffa506b9fa7beb17e2ea3e30f9cd028200787953ba186970005069",12750]
};

test('exact SHA256 for all production assets',async()=>{
 for(const [path,[sha,length]] of Object.entries(fixtures)){
  const res=await worker.fetch(new Request(root+path));
  assert.equal(res.status,200,path);
  const b=Buffer.from(await res.arrayBuffer());
  assert.equal(b.length,length,path);
  assert.equal(createHash('sha256').update(b).digest('hex'),sha,path);
  assert.equal(res.headers.get('x-content-type-options'),'nosniff');
  assert.match(res.headers.get('strict-transport-security')||'',/max-age=31536000/);
 }
});

test('homepage keeps hash-based script CSP',async()=>{
 const r=await worker.fetch(new Request(root+'/'));
 const txt=await r.text();
 assert.match(txt,/ACESSAR ARES/);
 assert.match(txt,/ABRIR CERBERUS/);
 const csp=r.headers.get('content-security-policy')||'';
 assert.match(csp,/sha256-/);
 assert.doesNotMatch(csp,/script-src 'unsafe-inline'/);
});

test('Cerberus gatekeeper uses hashes instead of unsafe-inline',async()=>{
 const r=await worker.fetch(new Request(root+'/cerberus-gatekeeper.html'));
 assert.equal(r.status,200);
 const csp=r.headers.get('content-security-policy')||'';
 assert.match(csp,/script-src 'sha256-/);
 assert.match(csp,/style-src 'sha256-/);
 assert.doesNotMatch(csp,/unsafe-inline/);
 assert.match(csp,/object-src 'none'/);
 assert.match(csp,/connect-src 'none'/);
});

test('HEAD, ETag and method/path denial remain deterministic',async()=>{
 let r=await worker.fetch(new Request(root+'/index.html',{method:'HEAD'}));
 assert.equal(r.status,200);assert.equal(await r.text(),'');
 const etag=(await worker.fetch(new Request(root+'/index.html'))).headers.get('etag');
 r=await worker.fetch(new Request(root+'/index.html',{headers:{'if-none-match':etag}}));
 assert.equal(r.status,304);
 assert.equal((await worker.fetch(new Request(root+'/.env'))).status,404);
 assert.equal((await worker.fetch(new Request(root+'/',{method:'POST'}))).status,405);
});
