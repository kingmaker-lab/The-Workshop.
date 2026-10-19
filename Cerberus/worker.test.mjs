import test from 'node:test';
import assert from 'node:assert/strict';
import worker from './worker.js';
const send=(path='/',method='GET')=>worker.fetch(new Request('https://cerberus.wolfpackworkshop.workers.dev'+path,{method}));
test('public home belongs to software architecture',async()=>{
 const r=await send();assert.equal(r.status,200);const html=await r.text();
 for(const mark of ['arquitetura de software','CERBERUS STATUS: ON','CERBERUS_01','CERBERUS_05','href="/labs/01"'])assert.ok(html.includes(mark),mark);
 for(const link of ['https://workshop-labs.pages.dev/projects/ares/','https://wolfpack-crypto.pages.dev/','https://wolfpack.wolfpackworkshop.workers.dev/'])assert.ok(html.includes('href="'+link+'"'));
 assert.doesNotMatch(html,/<script\b/i);assert.doesNotMatch(html,/<iframe\b/i);
});
test('first experiment presents trade-offs and an ADR',async()=>{
 const r=await send('/labs/01');assert.equal(r.status,200);const html=await r.text();
 assert.match(html,/monólito modular/i);assert.match(html,/Microsserviços/i);assert.match(html,/ADR/);
});
test('security headers and strict method & route handling',async()=>{
 const r=await send();const h=r.headers;
 for(const fragment of ["script-src 'none'","frame-ancestors 'none'","connect-src 'none'"])assert.ok(h.get('content-security-policy').includes(fragment));
 assert.equal(h.get('x-content-type-options'),'nosniff');assert.equal(h.get('x-frame-options'),'DENY');assert.equal(h.get('referrer-policy'),'no-referrer');
 assert.equal((await send('/.env')).status,404);
 const deny=await send('/','POST');assert.equal(deny.status,405);assert.equal(deny.headers.get('allow'),'GET, HEAD');
 const head=await send('/labs/01','HEAD');assert.equal(head.status,200);assert.equal(await head.text(),'');
});
test('public API is architecture-oriented and backward compatible',async()=>{
 const status=await (await send('/api/status')).json();assert.equal(status.status,'on');assert.equal(status.domain,'software_architecture');
 const modules=await (await send('/api/modules')).json();assert.equal(modules.modules.length,5);assert.equal(modules.modules[0].status,'available');
 const projects=await (await send('/api/projects')).json();assert.equal(projects.projects.length,4);
 assert.equal(projects.projects.find(p=>p.id==='cerberus').category,'software_architecture');
});
