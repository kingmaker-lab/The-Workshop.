import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import worker from './worker.mjs';

test('Ruby module runtime is allowed only on pinned CDN origin in worker-src', async () => {
  const response = await worker.fetch(new Request('https://wolfpack.wolfpackworkshop.workers.dev/'));
  const csp=response.headers.get('content-security-policy') || '';
  const directives=Object.fromEntries(csp.split(';').map(x=>x.trim().split(/\s+/)).filter(x=>x.length).map(x=>[x[0],x.slice(1)]));
  assert.deepEqual(directives['worker-src'],["'self'",'blob:','https://cdn.jsdelivr.net']);
  assert.ok(directives['script-src'].includes('https://cdn.jsdelivr.net'));
  assert.ok(directives['connect-src'].includes('https://cdn.jsdelivr.net'));
  assert.ok(directives['frame-ancestors'].includes("'none'"));
  assert.ok(directives['object-src'].includes("'none'"));
  assert.ok(directives['base-uri'].includes("'none'"));
  assert.ok(!csp.includes("'unsafe-eval'"));
  assert.ok(!csp.includes("'unsafe-inline'") || csp.includes("style-src 'self' 'unsafe-inline'"));
  assert.equal(response.headers.get('x-content-type-options'),'nosniff');
  assert.equal(response.headers.get('referrer-policy'),'no-referrer');
});

test('runtime loader bytes and content type are unchanged', async() => {
  const r=await worker.fetch(new Request('https://wolfpack.wolfpackworkshop.workers.dev/js/ruby-worker.js'));
  assert.equal(r.status,200);
  assert.match(r.headers.get('content-type'),/javascript/);
  const hash=createHash('sha256').update(Buffer.from(await r.arrayBuffer())).digest('hex');
  assert.equal(hash,'325c63f24f6fd69090794b72af164c56c1f2b46c2df12dfd4a0b711ae23e67d3');
});
