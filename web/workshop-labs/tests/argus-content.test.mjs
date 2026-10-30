import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import worker from '../_worker.js';

const source = readFileSync(fileURLToPath(new URL('../argus/index.html', import.meta.url)), 'utf8');
const fetchPage = (path='/', method='GET') =>
  worker.fetch(new Request('https://workshop-labs.pages.dev'+path,{method}));

test('ARGUS source of truth is identical to served HTML',async()=>{
  const response = await fetchPage('/argus/');
  assert.equal(response.status,200);
  assert.match(response.headers.get('content-type'),/^text\/html/);
  assert.equal(await response.text(),source);
  assert.equal((await fetchPage('/argus/index.html')).status,200);
  const head=await fetchPage('/argus/','HEAD');
  assert.equal(head.status,200);
  assert.equal(await head.text(),'');
});

test('ARGUS editorial sections are accessible and accurately scoped',async()=>{
  for(const id of ['visao','arquitetura','deteccoes','evidencia','telemetria','executar','seguranca','roadmap'])
    assert.ok(source.includes('id="'+id+'"'),'Missing '+id);
  for(const phrase of ['15 falhas em 30 segundos','Welford','17','03','SQLite',
    'JSONL','syslog','Zeek','127.0.0.1:8765','enabled: false',
    'Vitrine estática','LAB ONLY','python -m argus.main analyze',
    'python -m argus.main timeline','python -m argus.main serve'])
    assert.ok(source.includes(phrase),'Missing '+phrase);
  assert.ok(source.includes('href="/heartai/#playground"'));
  assert.ok(source.includes('href="https://github.com/kingmaker-lab/The-Workshop./tree/main/argus"'));
  assert.ok(source.includes('aria-label="Navegação do ARGUS"'));
  assert.ok(source.includes('href="#conteudo"'));
});

test('ARGUS remains static with defensive CSP; sibling labs are untouched',async()=>{
  const r=await fetchPage('/argus/');
  const csp=r.headers.get('content-security-policy');
  assert.ok(csp.includes("script-src 'none'"));
  assert.ok(csp.includes("connect-src 'none'"));
  assert.ok(csp.includes("frame-ancestors 'none'"));
  assert.ok(csp.includes("style-src 'unsafe-inline'"));
  assert.equal(r.headers.get('x-frame-options'),'DENY');
  assert.equal(r.headers.get('x-content-type-options'),'nosniff');
  assert.doesNotMatch(source,/<script\b/i);
  assert.doesNotMatch(source,/<iframe\b/i);
  assert.doesNotMatch(source,/<form\b/i);
  assert.equal((await fetchPage('/argus/','POST')).status,405);
  assert.equal((await fetchPage('/argus/secret')).status,404);
  const home=await (await fetchPage('/')).text();
  assert.ok(home.includes('CERBERUS PROTOCOL'));
  assert.ok(home.includes('href="/heartai/#playground"'));
  const heart=await (await fetchPage('/heartai/')).text();
  assert.ok(heart.includes('Tokenizer Playground.'));
  assert.ok(heart.includes('Neural Embeddings Playground.'));
});
