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

test('ARGUS v0.3 educational page documents local-only streaming controls',async()=>{
  const html=await (await fetchPage('/argus/')).text();
  for(const phrase of [
    'ARGUS v0.3 / CONTINUOUS INGEST',
    'id="continuo"',
    'href="#continuo"',
    'watch',
  ]) assert.ok(html.includes(phrase),'Missing '+phrase);
  for(const phrase of [
    '64 KiB por linha',
    '50.000 linhas completas',
    'uma nova geração',
    'python -m argus.main watch',
    '--poll-interval 0.5',
    '--from-end',
    '--max-lines',
    'estado de correlação e as baselines continuam em memória'
  ]) assert.ok(html.includes(phrase),'Missing '+phrase);
  assert.ok(html.includes('ENTREGUE / v0.3'));
  assert.ok(html.includes('Sigma Subset')); // v0.4 delivered the previously planned stage
  assert.doesNotMatch(html,/<script\b/i);
  const response=await fetchPage('/argus/');
  assert.ok(response.headers.get('content-security-policy').includes("script-src 'none'"));
  assert.ok(response.headers.get('content-security-policy').includes("connect-src 'none'"));
});

test('ARGUS v0.4 Sigma page stays static, opt-in and scoped', async () => {
  const response = await fetchPage('/argus/');
  assert.equal(response.status, 200);
  const html = await response.text();
  for (const phrase of [
    'id="sigma"', 'href="#sigma"', 'ARGUS v0.4 / SIGMA SUBSET',
    'v0.4 / LAB', 'Regras abertas. Interpretação controlada.',
    'python -m argus.main sigma-validate', 'config-sigma-demo.yaml',
    'sigma.enabled: false', 'product: argus',
    'category: authentication', 'Até 32 regras locais',
    'Não é um conversor completo', 'ESPECIFICAÇÃO SIGMA',
    'HEARTAI LAB',
  ]) {
    assert.ok(html.includes(phrase), phrase);
  }
  assert.doesNotMatch(html, /<script\b/i);
  const csp = response.headers.get('content-security-policy');
  assert.ok(csp.includes("script-src 'none'"));
  assert.ok(csp.includes("connect-src 'none'"));
  assert.equal((await fetchPage('/heartai/')).status, 200);
  assert.equal((await fetchPage('/argus/', 'POST')).status, 405);
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
