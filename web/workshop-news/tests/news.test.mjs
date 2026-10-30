import test from 'node:test';
import assert from 'node:assert/strict';
import worker from '../_worker.js';

const url = 'https://workshop-news.pages.dev';
const request = (path = '/', method = 'GET') => new Request(url + path, {method});

test('ARGUS article is local static HTML with restrictive CSP', async () => {
  const response = await worker.fetch(request('/argus/'));
  assert.equal(response.status, 200);
  assert.equal(response.headers.get('x-frame-options'), 'DENY');
  assert.ok(response.headers.get('content-security-policy').includes("script-src 'none'"));
  const html = await response.text();
  for (const marker of ['ARGUS v0.2', 'Welford', '17 testes aprovados', 'desativado por padrão']) {
    assert.ok(html.includes(marker));
  }
  assert.equal((await worker.fetch(request('/argus/index.html','HEAD'))).status,200);
});

test('unknown POST requests are rejected without proxying', async () => {
  const response = await worker.fetch(request('/', 'POST'));
  assert.equal(response.status, 405);
  assert.equal(response.headers.get('allow'), 'GET, HEAD');
});

test('homepage preserves previous release and inserts ARGUS entry', async () => {
  const previous = globalThis.fetch;
  const captures = [];
  globalThis.fetch = async (destination, options) => {
    captures.push({destination: destination.toString(), options});
    return new Response('<html><div class="lab-links"></div><span class="tiny">/ 04</span></html>',
      {status:200,headers:{'content-type':'text/html','set-cookie':'internal=redacted'}});
  };
  try {
    const response = await worker.fetch(request('/?q=test'));
    assert.equal(response.status,200);
    const html = await response.text();
    assert.ok(html.includes('href="/argus/"'));
    assert.ok(html.includes('/ 05'));
    assert.equal(response.headers.has('set-cookie'),false);
    assert.equal(captures.length,1);
    assert.equal(captures[0].destination,'https://aae8ce82.workshop-news.pages.dev/?q=test');
    assert.equal(captures[0].options.method,'GET');
    assert.deepEqual(Object.keys(captures[0].options.headers),['accept']);
  } finally {
    globalThis.fetch = previous;
  }
});

test('static resources and errors keep upstream status', async () => {
  const previous = globalThis.fetch;
  globalThis.fetch = async () => new Response('not found',{status:404,headers:{'content-type':'text/plain'}});
  try {
    const response = await worker.fetch(request('/unknown'));
    assert.equal(response.status,404);
    assert.equal(await response.text(),'not found');
  } finally {
    globalThis.fetch = previous;
  }
});
