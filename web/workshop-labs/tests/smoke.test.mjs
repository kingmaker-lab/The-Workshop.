import test from 'node:test';
import assert from 'node:assert/strict';
import worker from '../_worker.js';

const base='https://workshop-labs.pages.dev/';
const fetchPage=(path='/',method='GET')=>worker.fetch(new Request(new URL(path,base),{method}));

test('GET: three correct absolute HTTPS destinations',async()=>{
 const r=await fetchPage(); assert.equal(r.status,200);
 const html=await r.text();
 for(const target of ['https://workshop-labs.pages.dev/projects/ares/','https://wolfpack-crypto.pages.dev/','https://wolfpack.wolfpackworkshop.workers.dev/']) assert.ok(html.includes('href="'+target+'"'));
 assert.ok(html.includes('CERBERUS')); assert.ok(!/<script\\b/i.test(html)); assert.ok(!/<iframe\\b/i.test(html));
});

test('response headers: deny scripts, frames and sniffing',async()=>{
 const r=await fetchPage();const h=r.headers;
 for(const fragment of ["script-src 'none'","frame-ancestors 'none'","connect-src 'none'"]) assert.ok(h.get('content-security-policy').includes(fragment));
 assert.equal(h.get('x-content-type-options'),'nosniff');
 assert.equal(h.get('x-frame-options'),'DENY');
 assert.equal(h.get('referrer-policy'),'no-referrer');
});

test('GET/HEAD, 404 and 405 are deterministic',async()=>{
 assert.equal((await fetchPage('/index.html')).status,200);
 const head=await fetchPage('/','HEAD');assert.equal(head.status,200);assert.equal(await head.text(),'');
 const absent=await fetchPage('/.env');assert.equal(absent.status,404);assert.ok((await absent.text()).includes('Not Found'));
 const post=await fetchPage('/','POST');assert.equal(post.status,405);assert.equal(post.headers.get('allow'),'GET, HEAD');
});
