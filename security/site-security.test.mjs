import test from 'node:test';
import assert from 'node:assert/strict';

import workshop from '../web/workshop-labs/_worker.js';
import crypto from '../sites/wolfpack-crypto/worker.mjs';
import ares from '../web/ares-site/_worker.js';
import cerberus from '../Cerberus/worker.js';
import wolfpack from '../web/wolfpack-os-v041-edge/worker.mjs';

const targets = [
  {name:'Workshop Labs',worker:workshop,origin:'https://workshop-labs.pages.dev'},
  {name:'Crypto Lab',worker:crypto,origin:'https://wolfpack-crypto.pages.dev'},
  {name:'ARES',worker:ares,origin:'https://workshop-labs.pages.dev'},
  {name:'Cerberus',worker:cerberus,origin:'https://cerberus.wolfpackworkshop.workers.dev'},
  {name:'WolfPack OS',worker:wolfpack,origin:'https://wolfpack.wolfpackworkshop.workers.dev'}
];
const send=(target,path='/',method='GET') =>
  target.worker.fetch(new Request(target.origin+path,{method,redirect:'manual'}));

for (const target of targets) {
  test(target.name+' security: GET/HEAD and mandatory headers', async()=>{
    const r=await send(target);
    assert.equal(r.status,200,'root GET');
    const h=r.headers;
    assert.equal(h.get('x-content-type-options'),'nosniff');
    assert.equal(h.get('x-frame-options'),'DENY');
    assert.ok(h.get('referrer-policy'));
    assert.match(h.get('strict-transport-security')||'',/max-age=\d+/);
    assert.match(h.get('permissions-policy')||'',/camera=\(\)/);
    const csp=h.get('content-security-policy')||'';
    assert.match(csp,/frame-ancestors 'none'/);
    assert.match(csp,/object-src 'none'/);
    assert.match(csp,/base-uri 'none'/);
    assert.doesNotMatch(csp,/unsafe-eval/);
    assert.equal(h.get('access-control-allow-origin'),null,'no unsolicited CORS');
    const head=await send(target,'/','HEAD');
    assert.equal(head.status,200);
    assert.equal(await head.text(),'');
  });
  test(target.name+' security: errors and sensitive path denial', async()=>{
    for(const method of ['POST','PUT','PATCH','DELETE','OPTIONS']){
      const r=await send(target,'/',method);
      assert.equal(r.status,405,method);
      assert.match(r.headers.get('allow')||'',/GET/);
      assert.equal(r.headers.get('cache-control'),'no-store',method+' cache');
      assert.equal(r.headers.get('access-control-allow-origin'),null);
    }
    for(const path of ['/.env','/.git/config','/not-a-real-route-82913','/%2e%2e/%2e%2e/secrets','/assets/never-here-82913.js']){
      const r=await send(target,path);
      assert.equal(r.status,404,path);
      assert.equal(r.headers.get('cache-control'),'no-store','no-store '+path);
      assert.equal(r.headers.get('access-control-allow-origin'),null);
    }
  });
  test(target.name+' security: no reflected query or open redirects',async()=>{
    const payload='WORKSHOP_XSS_PROBE_83"><script>alert(1)</script>';
    const r=await send(target,'/?q='+encodeURIComponent(payload)+'&next=https%3A%2F%2Fevil.invalid');
    assert.equal(r.status,200);
    assert.ok(!(await r.text()).includes(payload),'query must not be reflected');
    assert.equal(r.headers.get('location'),null);
  });
}
