import test from 'node:test';
import assert from 'node:assert/strict';
import worker from '../_worker.js';

const base = 'https://workshop-labs.pages.dev/';
const fetchPage = (path = '/', method = 'GET') =>
  worker.fetch(new Request(new URL(path, base), { method }));

test('homepage: five usable laboratory cards and accessible CERBERUS navigation', async () => {
  const response = await fetchPage();
  assert.equal(response.status, 200);
  const html = await response.text();
  const targets = [
    'https://github.com/kingmaker-lab/The-Workshop./tree/main/ares',
    'https://wolfpack-crypto.pages.dev/',
    'https://wolfpack.wolfpackworkshop.workers.dev/',
    '/argus/',
    'https://cerberus.wolfpackworkshop.workers.dev/',
  ];
  for (const target of targets) assert.ok(html.includes('href="' + target + '"'), target);
  assert.ok(html.includes('id="cerberus-card"'));
  assert.ok(html.includes('CERBERUS PROTOCOL'));
  assert.ok(html.includes('LABORATÓRIO DE ARQUITETURA DE SOFTWARE'));
  assert.ok(html.includes('href="#cerberus-card"'));
  assert.ok(html.includes('href="/assets/labs.css"'));
  assert.ok(!html.includes('href="https://workshop-labs.pages.dev/projects/ares/"'));
  assert.ok(!/<script\b/i.test(html));
  assert.ok(!/<iframe\b/i.test(html));
  assert.ok(!/<style\b/i.test(html));
});

test('homepage security: strong response headers, no inline scripts or styles', async () => {
  const response = await fetchPage();
  const h = response.headers, csp = h.get('content-security-policy');
  for (const directive of [
    "default-src 'none'", "script-src 'none'", "style-src 'self'",
    "connect-src 'none'", "frame-ancestors 'none'", "form-action 'none'",
  ]) assert.ok(csp.includes(directive), directive);
  assert.ok(!csp.includes('unsafe-inline'));
  assert.equal(h.get('x-content-type-options'), 'nosniff');
  assert.equal(h.get('x-frame-options'), 'DENY');
  assert.equal(h.get('referrer-policy'), 'no-referrer');
  assert.equal(h.get('cross-origin-opener-policy'), 'same-origin');
  assert.equal(h.get('cross-origin-resource-policy'), 'same-origin');
  assert.equal(h.get('x-permitted-cross-domain-policies'), 'none');
  assert.ok(h.get('strict-transport-security').includes('max-age='));
});

test('same-origin CSS asset: content type and deterministic HEAD/GET', async () => {
  const css = await fetchPage('/assets/labs.css');
  assert.equal(css.status, 200);
  assert.match(css.headers.get('content-type'), /^text\/css/);
  assert.ok((await css.text()).includes('.card.cerberus'));
  const head = await fetchPage('/assets/labs.css', 'HEAD');
  assert.equal(head.status, 200);
  assert.equal(await head.text(), '');
});

test('method and route restrictions: no sensitive files or unexpected methods', async () => {
  const index = await fetchPage('/index.html');
  assert.equal(index.status, 200);
  assert.equal(await (await fetchPage('/', 'HEAD')).text(), '');
  for (const path of ['/.env', '/.git/config', '/server.js', '/api/config', '/cerberus/']) {
    const response = await fetchPage(path);
    assert.equal(response.status, 404, path);
    assert.equal(response.headers.get('cache-control'), 'no-store');
    assert.match(response.headers.get('content-type'), /^text\/plain/);
  }
  const post = await fetchPage('/', 'POST');
  assert.equal(post.status, 405);
  assert.equal(post.headers.get('allow'), 'GET, HEAD');
  assert.equal(post.headers.get('cache-control'), 'no-store');
  assert.match(post.headers.get('content-type'), /^text\/plain/);
});

test('ARGUS remains available with its isolated legacy inline CSS exception', async () => {
  const response = await fetchPage('/argus/');
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.ok(html.includes('Vitrine estática'));
  assert.ok(html.includes('Welford'));
  assert.ok(!/<script\b/i.test(html));
  assert.ok(response.headers.get('content-security-policy').includes("script-src 'none'"));
  assert.ok(response.headers.get('content-security-policy').includes("style-src 'unsafe-inline'"));
  assert.equal((await fetchPage('/argus/index.html')).status, 200);
  assert.equal((await fetchPage('/argus/', 'HEAD')).status, 200);
});
