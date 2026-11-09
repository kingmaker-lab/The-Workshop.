import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import worker from '../_worker.js';
const base='https://workshop-labs.pages.dev/';
const go=(path,method='GET')=>worker.fetch(new Request(new URL(path,base),{method}));
test('NEXUS linked without removing other labs',async()=>{
 const response=await go('/');assert.equal(response.status,200);
 const html=await response.text();
 for(const value of ['href="/nexus/"','ARGUS PROJECT','HEARTAI / TOKENIZER','CERBERUS PROTOCOL','CRYPTO LAB']) assert.ok(html.includes(value),value);
 assert.ok(!/<script\b/i.test(html));
});
test('NEXUS page source mirror and read-only route safety',async()=>{
 const response=await go('/nexus/');
 assert.equal(response.status,200);
 const html=await response.text();
 assert.equal(html,readFileSync(new URL('../nexus/index.html',import.meta.url),'utf8'));
 for(const val of ['NEXUS-06','0,9158','0,9122','EXP-007','Elman venceu 7 vezes']) assert.ok(html.includes(val),val);
 assert.ok(!/<script\b/i.test(html));
 assert.ok(!/<style\b/i.test(html));
 assert.ok(response.headers.get('content-security-policy').includes("script-src 'none'"));
 for(const path of ['/nexus','/nexus/index.html']) assert.equal((await go(path)).status,200);
 const head=await go('/nexus/','HEAD');assert.equal(head.status,200);assert.equal(await head.text(),'');
 const post=await go('/nexus/','POST');assert.equal(post.status,405);
});
