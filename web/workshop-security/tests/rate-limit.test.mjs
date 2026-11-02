import test from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {fileURLToPath,pathToFileURL} from 'node:url';
import path from 'node:path';
import {readFile} from 'node:fs/promises';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
execFileSync(process.execPath,[path.join(root,'build.mjs')],{stdio:'pipe'});
const worker=(await import(pathToFileURL(path.join(root,'dist/worker.mjs')).href+'?rate-limit-test='+Date.now())).default;
const base='https://workshop-security.example';
const deny={limit:async()=>({success:false})};

function post(route,body,env={}){
 return worker.fetch(new Request(base+route,{method:'POST',headers:{Origin:base,'Content-Type':'application/json','CF-Connecting-IP':'198.51.100.50'},body:JSON.stringify(body)}),{DB:{},...env});
}

test('distributed auth limiter rejects session creation before touching D1',async()=>{
 const r=await post('/api/session',{nickname:'wolf_01'},{CTF_AUTH_LIMITER:deny});
 assert.equal(r.status,429);
 assert.equal(r.headers.get('Retry-After'),'60');
 assert.equal(r.headers.get('Cache-Control'),'no-store');
});

test('distributed auth limiter also covers recovery',async()=>{
 const r=await post('/api/restore',{nickname:'wolf_01',recovery:'A'.repeat(32)},{CTF_AUTH_LIMITER:deny});
 assert.equal(r.status,429);
 assert.equal(r.headers.get('Retry-After'),'60');
});

test('distributed submit limiter rejects flag bursts before session lookup',async()=>{
 const r=await post('/api/submit',{id:'base64',flag:'WS{000000000000000000}'},{CTF_SUBMIT_LIMITER:deny});
 assert.equal(r.status,429);
 assert.equal(r.headers.get('Retry-After'),'60');
});

test('wrangler keeps D1/secret model and adds isolated limiter namespaces plus observability',async()=>{
 const toml=await readFile(path.join(root,'wrangler.toml'),'utf8');
 assert.match(toml,/binding = "DB"/);
 assert.match(toml,/FLAG_SECRET/);
 assert.match(toml,/name = "CTF_AUTH_LIMITER"/);
 assert.match(toml,/name = "CTF_SUBMIT_LIMITER"/);
 assert.match(toml,/head_sampling_rate = 0\.1/);
 assert.match(toml,/redact_query_string = true/);
});

test('static security baseline now includes HSTS',async()=>{
 const r=await worker.fetch(new Request(base+'/'),{});
 assert.equal(r.status,200);
 assert.match(r.headers.get('Strict-Transport-Security')||'',/max-age=31536000/);
});


test('D1 observability classifies failures without logging exception or request content',async()=>{
 const source=await readFile(path.join(root,'worker.mjs'),'utf8');
 assert.match(source,/d1_failure/);
 assert.match(source,/String\(e\?\.message\|\|''\)/);
 assert.doesNotMatch(source,/console\.error\([^;\n]*e\?\.message/);
 assert.doesNotMatch(source,/console\.error\([^;\n]*body\./);
});
