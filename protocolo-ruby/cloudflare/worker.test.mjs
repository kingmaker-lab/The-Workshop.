import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

const source=await readFile(new URL('./worker.js',import.meta.url),'utf8');
const worker=(await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'))).default;

test('Protocolo Ruby Worker uses hashed CSP without unsafe-inline',async()=>{
  assert.doesNotMatch(source,/unsafe-inline/);
  assert.match(source,/script-src 'sha256-/);
  assert.match(source,/style-src 'sha256-/);
  const r=await worker.fetch(new Request('https://protocolo-ruby.example/'));
  assert.equal(r.status,200);
  const csp=r.headers.get('content-security-policy')||'';
  assert.doesNotMatch(csp,/unsafe-inline/);
  assert.match(csp,/script-src 'sha256-/);
  assert.match(csp,/style-src 'sha256-/);
  assert.match(csp,/upgrade-insecure-requests/);
});

test('HSTS and no-store survive home and error responses',async()=>{
  const home=await worker.fetch(new Request('https://protocolo-ruby.example/'));
  assert.match(home.headers.get('strict-transport-security')||'',/max-age=31536000/);
  assert.equal(home.headers.get('cache-control'),'no-store');
  const missing=await worker.fetch(new Request('https://protocolo-ruby.example/not-found'));
  assert.equal(missing.status,404);
  assert.match(missing.headers.get('strict-transport-security')||'',/max-age=31536000/);
  assert.equal(missing.headers.get('cache-control'),'no-store');
});

test('gateway remains fixed-route GET-only and has no arbitrary proxy target',()=>{
  assert.match(source,/\['\/backend\/health','\/backend\/capabilities','\/backend\/demo'\]/);
  assert.match(source,/https:\/\/protocolo-ruby-api\.onrender\.com/);
  assert.doesNotMatch(source,/fetch\s*\(\s*req\.url/);
  assert.doesNotMatch(source,/fetch\s*\(\s*p\s*\)/);
  assert.doesNotMatch(source,/fetch\s*\(\s*new URL/);
  assert.doesNotMatch(source,/Access-Control-Allow-Origin/i);
  assert.doesNotMatch(source,/\beval\s*\(|new\s+Function\s*\(/);
});
