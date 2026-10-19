import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import worker from './worker.mjs';
const root='https://wolfpack.wolfpackworkshop.workers.dev';
const fixtures={
'/index.html':['1c9bcb38de1c93d786b7ee0ef135172aa934e772169736cffa034fa7507a6d0e',132926],
'/js/ruby-worker.js':['325c63f24f6fd69090794b72af164c56c1f2b46c2df12dfd4a0b711ae23e67d3',3858],
'/downloads/raven-ruby-v0.1-original.zip':['ab3afe7a51cbf62fd1e2a5ff8a17797e00678370f4070e843afb032ecb5a82ac',8795],
'/downloads/vulpes77-terminal-v0.1-original.zip':['106738b06d7adda787ad3526f0fc1fb3b53aeeaf783c93da8cdbbad179acf245',13045],
'/downloads/wolfpack-ruby-protocol-v0.1.zip':['7d41e5747111cc1159cd947e8613d16893b042b9bd36bd1d3e2dc89fbfe3c054',16274]};
test('exact SHA256 for all five assets',async()=>{
 for(const [path,[sha,length]] of Object.entries(fixtures)){
  const res=await worker.fetch(new Request(root+path));
  assert.equal(res.status,200,path);const b=Buffer.from(await res.arrayBuffer());
  assert.equal(b.length,length,path);
  assert.equal(createHash('sha256').update(b).digest('hex'),sha,path);
  assert.equal(res.headers.get('x-content-type-options'),'nosniff');
 }
});
test('homepage markup and Content-Security-Policy hash-based inline scripts',async()=>{
 const r=await worker.fetch(new Request(root+'/'));let txt=await r.text();
 assert.match(txt,/app-card" href="https:\/\/workshop-labs.pages.dev\/projects\/ares\//);
 assert.match(txt,/app-card" href="https:\/\/cerberus.wolfpackworkshop.workers.dev\//);
 assert.match(txt,/RAVEN Drift Lab/);assert.match(txt,/id="raven-drift-engine"/);
 assert.ok(r.headers.get('content-security-policy').includes('sha256-'));
 assert.ok(!r.headers.get('content-security-policy').includes("script-src 'unsafe-inline'"));
});
test('HEAD and If-None-Match',async()=>{
 let r=await worker.fetch(new Request(root+'/index.html',{method:'HEAD'}));assert.equal(r.status,200);assert.equal(await r.text(),'');
 r=await worker.fetch(new Request(root+'/index.html',{headers:{'if-none-match':fixtures['/index.html'][0].replace(/^|$/g,'"')}}));assert.equal(r.status,304);
});
test('no unexpected methods or paths',async()=>{
 assert.equal((await worker.fetch(new Request(root+'/dashboard'))).status,404);
 assert.equal((await worker.fetch(new Request(root+'/.env'))).status,404);
 assert.equal((await worker.fetch(new Request(root+'/',{method:'POST'}))).status,405);
});
