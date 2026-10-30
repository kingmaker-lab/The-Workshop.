import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import { TextEncoder } from 'node:util';
import worker from '../_worker.js';

const base = 'https://workshop-labs.pages.dev/';
const fetchRoute = (path, method='GET') =>
  worker.fetch(new Request(new URL(path,base), {method}));

test('HeartAI tokenizer and original ARGUS coexist on independent routes', async () => {
  const home = await (await fetchRoute('/')).text();
  assert.ok(home.includes('href="/heartai/#playground"'));
  assert.ok(home.includes('href="/argus/"'));
  const heart = await fetchRoute('/heartai/');
  assert.equal(heart.status,200);
  assert.equal(heart.headers.get('x-frame-options'),'DENY');
  const html = await heart.text();
  assert.ok(html.includes('Tokenizer Playground.'));
  assert.ok(html.includes('id="input"'));
  assert.ok(html.includes('id="output"'));
  assert.ok(html.includes('src="/heartai/tokenizer.js"'));
  assert.ok(heart.headers.get('content-security-policy').includes("script-src 'self'"));
  assert.ok(heart.headers.get('content-security-policy').includes("connect-src 'none'"));
  assert.equal((await fetchRoute('/heartai','HEAD')).status,200);
  assert.equal((await fetchRoute('/heartai/index.html')).status,200);
  const argus = await (await fetchRoute('/argus/')).text();
  assert.ok(argus.includes('ARGUS'));
  assert.ok(argus.includes('href="/heartai/#playground"'));
  const oldLink = await fetchRoute('/argus/tokenizer');
  assert.equal(oldLink.status,308);
  assert.equal(oldLink.headers.get('location'),'/heartai/#playground');
});

test('restored tokenizer script works locally with UTF-8 and BPE merging', async () => {
  const script = await fetchRoute('/heartai/tokenizer.js');
  assert.equal(script.status, 200);
  assert.match(script.headers.get('content-type'), /^application\/javascript/);
  assert.ok(script.headers.get('content-security-policy').includes("script-src 'none'"));
  const source = await script.text();
  assert.ok(source.includes('TextEncoder'));
  assert.ok(source.includes('function encode'));
  assert.ok(!/\bfetch\s*\(/.test(source));
  const node = () => ({
    children:[],
    textContent:'',
    value:'',
    append(...items){this.children.push(...items);},
    addEventListener(event,callback){this.listeners ??= {};this.listeners[event]=callback;},
  });
  const input = node(), output = node(), stats = node(), timeline = node();
  input.value = 'Olá, HeartAI! 🦊';
  const elements = {input,output,stats,timeline};
  const document = {
    getElementById: id => elements[id],
    createElement: () => node(),
  };
  vm.runInNewContext(source,{TextEncoder,document},{timeout:1000});
  assert.equal(timeline.children.length,10);
  const tokens = JSON.parse(output.textContent);
  assert.ok(tokens.length>0);
  assert.ok(tokens.every(id=>Number.isInteger(id)&&id>=0));
  assert.ok(stats.textContent.includes('TOKENS:'));
  input.value='heartai heartai heartai';
  input.listeners.input();
  const merged=JSON.parse(output.textContent);
  assert.ok(merged.length < new TextEncoder().encode(input.value).length);
});

test('HTTP hardening stays effective outside the interactive tokenizer page', async () => {
  for(const path of ['/','/argus/']){
    const r=await fetchRoute(path);
    assert.equal(r.status,200);
    assert.ok(r.headers.get('content-security-policy').includes("script-src 'none'"));
  }
  assert.equal((await fetchRoute('/.env')).status,404);
  assert.equal((await fetchRoute('/heartai/tokenizer.js','HEAD')).status,200);
  assert.equal((await fetchRoute('/heartai/tokenizer.js','POST')).status,405);
});
