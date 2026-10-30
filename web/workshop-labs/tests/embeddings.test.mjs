import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import { TextEncoder } from 'node:util';
import worker from '../_worker.js';

const base = 'https://workshop-labs.pages.dev';
const fetchLocal = (path, method = 'GET') =>
  worker.fetch(new Request(base + path, { method }));

test('HEART_004 and tokenizer playground remain present with local-only scripts', async () => {
  const htmlResponse = await fetchLocal('/heartai/');
  assert.equal(htmlResponse.status, 200);
  const html = await htmlResponse.text();
  for (const phrase of ['Tokenizer Playground.', 'Neural Embeddings Playground.', 'id="embedding-a"',
    'id="embedding-b"', 'src="/heartai/tokenizer.js"', 'src="/heartai/embeddings.js"']) {
    assert.ok(html.includes(phrase), phrase);
  }
  const csp = htmlResponse.headers.get('content-security-policy');
  assert.ok(csp.includes("script-src 'self'"));
  assert.ok(csp.includes("connect-src 'none'"));
  assert.ok(csp.includes("frame-ancestors 'none'"));
  const js = await fetchLocal('/heartai/embeddings.js');
  assert.equal(js.status, 200);
  assert.match(js.headers.get('content-type'), /^application\/javascript/);
  assert.ok(js.headers.get('x-content-type-options') === 'nosniff');
  assert.equal((await fetchLocal('/heartai/embeddings.js', 'HEAD')).status, 200);
  assert.equal((await fetchLocal('/heartai/embeddings.js', 'POST')).status, 405);
  const original = await (await fetchLocal('/argus/')).text();
  assert.ok(original.includes('ARGUS'));
  const home = await (await fetchLocal('/')).text();
  assert.ok(home.includes('/heartai/#playground'));
  assert.ok(home.includes('/argus/'));
});

test('HEART_004 browser model initializes and computes deterministic vector similarity', async () => {
  const tokenizer = await (await fetchLocal('/heartai/tokenizer.js')).text();
  const embeddings = await (await fetchLocal('/heartai/embeddings.js')).text();
  assert.ok(!/\bfetch\s*\(/.test(embeddings));
  assert.ok(!/\b(?:eval|Function)\s*\(/.test(embeddings));
  const makeNode = () => ({
    textContent: '', value: '',
    children: [],
    append(...xs) { this.children.push(...xs); },
    addEventListener(name, fn) { (this.listeners ??= {})[name] = fn; }
  });
  const elements = {
    input: makeNode(), output: makeNode(), stats: makeNode(), timeline: makeNode(),
    'embedding-a': makeNode(), 'embedding-b': makeNode(),
    'embedding-vector': makeNode(), 'embedding-score': makeNode(),
  };
  elements.input.value = 'Olá, HeartAI! 🦊';
  elements['embedding-a'].value = 'heartai aprende tokens';
  elements['embedding-b'].value = 'linguagem neural';
  const document = {
    getElementById(name) { return elements[name]; },
    createElement() { return makeNode(); }
  };
  const context = vm.createContext({ document, TextEncoder });
  vm.runInContext(tokenizer, context, {timeout: 1000});
  vm.runInContext(embeddings, context, {timeout: 3000});
  assert.match(elements['embedding-score'].textContent, /Similaridade de cosseno:/);
  assert.match(elements['embedding-vector'].textContent, /^\[ /);
  assert.ok(!elements['embedding-score'].textContent.includes('NaN'));
  assert.equal(elements.timeline.children.length, 10);
  assert.ok(elements.timeline.children[3].children.some(x => x.textContent === 'IMPLEMENTADO'));
  const old = elements['embedding-score'].textContent;
  elements['embedding-b'].value = 'heartai aprende tokens';
  elements['embedding-b'].listeners.input();
  assert.notEqual(elements['embedding-score'].textContent, old);
  assert.match(elements['embedding-score'].textContent, /1\.0000/);
});
