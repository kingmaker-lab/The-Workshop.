import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import worker from '../_worker.js';

const base='https://workshop-labs.pages.dev/';
const request=(path,method='GET')=>worker.fetch(new Request(new URL(path,base),{method}));
const report=readFileSync(new URL('../nexus/exp009/index.html',import.meta.url),'utf8');
const css=readFileSync(new URL('../nexus/exp009/report.css',import.meta.url),'utf8');
const nexus=readFileSync(new URL('../nexus/index.html',import.meta.url),'utf8');

test('EXP-009 is source mirrored and accessible without altering historical NEXUS',async()=>{
 const r=await request('/nexus/exp009/');
 assert.equal(r.status,200);
 assert.equal(await r.text(),report);
 assert.equal((await (await request('/nexus/exp009/index.html')).text()),report);
 assert.ok(report.includes('18 / 18')&&report.includes('6 / 9'));
 assert.ok(report.includes('−0,02934')&&report.includes('+0,00380'));
 assert.ok(report.includes('23/11/2026'));
 assert.ok(report.includes('não constituem validação externa'));
 const p=await request('/nexus/');
 assert.equal(p.status,200);
 assert.equal(await p.text(),nexus);
 for(const oldText of ['EXP-006','EXP-007','EXP-008','0,9158','0,9122','536 alvos','0,9176','NEXUS-06']) {
  assert.ok(nexus.includes(oldText),oldText);
 }
 assert.ok(nexus.includes('href="/nexus/exp009/"'));
});

test('EXP-009 content does not execute scripts, ingest user data or load external resources',()=>{
 assert.doesNotMatch(report,/<(?:script|iframe|form|style)\b/i);
 assert.doesNotMatch(report,/\bon\w+\s*=/i);
 assert.doesNotMatch(report,/\b(?:fetch|XMLHttpRequest|WebSocket|eval)\s*\(/i);
 assert.doesNotMatch(report,/<(?:img|link|script)[^>]+(?:src|href)\s*=\s*["']https?:/i);
 assert.ok(report.includes('rel="noopener noreferrer"'));
 assert.ok(report.includes('scope="row"')&&report.includes('<caption>'));
 assert.ok(!report.includes('private_key')&&!report.includes('api_key'));
});

test('EXP-009 route uses strict inherited security headers and only GET/HEAD',async()=>{
 const r=await request('/nexus/exp009/');
 const h=r.headers;
 assert.match(h.get('content-type'),/^text\/html/);
 for(const item of [
  "default-src 'none'", "script-src 'none'", "style-src 'self'",
  "connect-src 'none'", "form-action 'none'", "frame-ancestors 'none'",
  "base-uri 'none'", "object-src 'none'"
 ]) assert.ok(h.get('content-security-policy').includes(item),item);
 assert.equal(h.get('x-content-type-options'),'nosniff');
 assert.equal(h.get('x-frame-options'),'DENY');
 assert.equal(h.get('referrer-policy'),'no-referrer');
 assert.equal(h.get('cross-origin-opener-policy'),'same-origin');
 assert.equal(h.get('cross-origin-resource-policy'),'same-origin');
 assert.equal(h.get('x-permitted-cross-domain-policies'),'none');
 assert.match(h.get('strict-transport-security'),/max-age=\d+/);
 assert.ok(h.get('permissions-policy').includes('camera=()'));
 const head=await request('/nexus/exp009/','HEAD');
 assert.equal(head.status,200);
 assert.equal(await head.text(),'');
 assert.equal(head.headers.get('content-security-policy'),h.get('content-security-policy'));
 const post=await request('/nexus/exp009/','POST');
 assert.equal(post.status,405);
 assert.equal(post.headers.get('allow'),'GET, HEAD');
 const put=await request('/nexus/exp009/report.css','PUT');
 assert.equal(put.status,405);
 const redirect=await request('/nexus/exp009');
 assert.equal(redirect.status,308);
 assert.equal(redirect.headers.get('location'),'/nexus/exp009/');
 assert.equal((await request('/nexus/exp009/secret')).status,404);
});

test('EXP-009 styles are same-origin, nosniff and source-mirrored',async()=>{
 const r=await request('/nexus/exp009/report.css');
 assert.equal(r.status,200);
 assert.match(r.headers.get('content-type'),/^text\/css/);
 assert.equal(r.headers.get('x-content-type-options'),'nosniff');
 assert.equal(await r.text(),css);
 assert.ok(css.includes('.report-table'));
 assert.equal((await request('/nexus/exp009/report.css','HEAD')).status,200);
});

test('Existing routes and sensitive-path restrictions still operate',async()=>{
 for(const path of ['/','/nexus/','/argus/','/heartai/','/assets/labs.css',
  '/crypto-lab/','/crypto-lab/pow/','/crypto-lab/signatures/',
  '/crypto-lab/pow/miner.worker.js','/crypto-lab/signatures/protocol.js']){
  const r=await request(path);
  assert.equal(r.status,200,path);
 }
 for(const path of ['/.env','/.git/config','/api/config','/nexus/exp009/data.json']){
  assert.equal((await request(path)).status,404,path);
 }
 const home=await (await request('/')).text();
 for(const target of ['id="blockchain-experiments"','CERBERUS PROTOCOL','ARGUS PROJECT','NEXUS-06 NEURAL LAB','HEARTAI / TOKENIZER']){
  assert.ok(home.includes(target),target);
 }
});
