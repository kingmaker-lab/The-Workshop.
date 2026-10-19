import test from 'node:test';
import assert from 'node:assert/strict';
import worker from './worker.js';
const base = 'https://cerberus.wolfpackworkshop.workers.dev/';
const send=(path='/',method='GET')=>worker.fetch(new Request(new URL(path,base),{method}));
test('Cerberus home exposes absolute HTTPS links',async()=>{
 const r=await send();assert.equal(r.status,200);
 const html=await r.text();
 for(const host of ['https://wolfpack.wolfpackworkshop.workers.dev/','https://workshop-labs.pages.dev/projects/ares/','https://wolfpack-crypto.pages.dev/']) assert.ok(html.includes('href="'+host+'"'));
 assert.ok(html.includes('CERBERUS STATUS: ON'));assert.ok(!/<script\\b/i.test(html));assert.ok(!/<iframe\\b/i.test(html));
});
test('CSP and secure response headers',async()=>{const r=await send();const h=r.headers;for(const part of ["script-src 'none'","connect-src 'none'","frame-ancestors 'none'"])assert.ok(h.get('content-security-policy').includes(part));assert.equal(h.get('referrer-policy'),'no-referrer');assert.equal(h.get('x-content-type-options'),'nosniff');});
test('health and project registry',async()=>{const s=await send('/api/status');assert.equal(s.status,200);assert.equal((await s.json()).status,'on');const r=await send('/api/projects');assert.equal(r.status,200);const d=await r.json();assert.equal(d.projects.length,4);assert.equal(d.projects.find(x=>x.id==='cerberus').status,'online');});
test('method and unknown paths',async()=>{assert.equal((await send('/.env')).status,404);assert.equal((await send('/','POST')).status,405);const head=await send('/api/status','HEAD');assert.equal(head.status,200);assert.equal(await head.text(),'');});
