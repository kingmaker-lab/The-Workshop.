import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import { TextEncoder } from 'node:util';
import worker from '../_worker.js';

const origin = 'https://workshop-labs.pages.dev';
const request = (path, method='GET') =>
  worker.fetch(new Request(origin + path, {method}));

function simulate(original='HeartAI aprende atenção') {
  function createElement(tag='div') {
    let text = '';
    const element = {
      tagName: tag, children: [], attributes: {}, listeners: {},
      value: '', max: '', className: '',
      append(...items) { this.children.push(...items); },
      setAttribute(name, value) { this.attributes[name] = value; },
      addEventListener(name, handler) { this.listeners[name] = handler; }
    };
    Object.defineProperty(element, 'textContent', {
      get() { return text; },
      set(value) { text = String(value); this.children = []; }
    });
    return element;
  }
  const ids = ['input', 'output', 'stats', 'timeline',
    'attention-input', 'attention-matrix', 'attention-focus',
    'attention-stats', 'attention-detail'];
  const elements = Object.fromEntries(ids.map(id => [id, createElement()]));
  elements.input.value = 'Olá, HeartAI! 🦊';
  elements['attention-input'].value = original;
  elements['attention-focus'].value = '0';
  const document = {
    getElementById(id) { return elements[id] ?? null; },
    createElement
  };
  const context = vm.createContext({ document, TextEncoder });
  return {elements, context};
}

test('HEART_005 is served locally with strict routing, CSP, and intact labs', async () => {
  const htmlResponse = await request('/heartai/');
  assert.equal(htmlResponse.status, 200);
  const html = await htmlResponse.text();
  for(const phrase of [
    'Tokenizer Playground.', 'Neural Embeddings Playground.',
    'Causal Attention Playground.', 'id="attention-input"',
    'id="attention-focus"', 'id="attention-matrix"',
    'src="/heartai/tokenizer.js"', 'src="/heartai/embeddings.js"',
    'src="/heartai/attention.js"', 'href="#attention"',
    'não foram treinadas', 'Não gera texto'
  ]) assert.ok(html.includes(phrase), phrase);
  const csp=htmlResponse.headers.get('content-security-policy');
  assert.ok(csp.includes("script-src 'self'"));
  assert.ok(csp.includes("connect-src 'none'"));
  assert.ok(csp.includes("frame-ancestors 'none'"));

  const js = await request('/heartai/attention.js');
  assert.equal(js.status, 200);
  assert.match(js.headers.get('content-type'), /^application\/javascript/);
  assert.equal(js.headers.get('x-content-type-options'), 'nosniff');
  const source = await js.text();
  assert.doesNotMatch(source, /\b(fetch|XMLHttpRequest|WebSocket|eval)\s*\(/);
  assert.equal((await request('/heartai/attention.js','HEAD')).status, 200);
  assert.equal((await request('/heartai/attention.js','POST')).status, 405);
  assert.equal((await request('/heartai/unknown.js')).status, 404);
  assert.ok((await (await request('/argus/')).text()).includes('ARGUS'));
  assert.ok((await (await request('/')).text()).includes('CERBERUS PROTOCOL'));
  assert.equal((await request('/nexus/')).status, 200);
});

test('HEART_005 browser heatmap is causal, deterministic, and interactive', async () => {
  const {elements, context} = simulate('ABCD');
  for(const path of ['/heartai/tokenizer.js', '/heartai/attention.js']) {
    const script = await (await request(path)).text();
    vm.runInContext(script, context, {timeout: 3000});
  }
  const mat = elements['attention-matrix'];
  const initial = mat.children[0];
  assert.equal(initial.tagName, 'table');
  assert.match(elements['attention-stats'].textContent,/MÁSCARA: causal/);
  assert.equal(elements.timeline.children.length, 10);
  assert.equal(elements.timeline.children[4].children[1].textContent, 'IMPLEMENTADO');
  assert.equal(initial.children.length, 5); // header + 4 bytes
  for(let i=0;i<4;i++){
    const cells=initial.children[i+1].children;
    assert.equal(cells.length, 5);
    let sum=0;
    for(let j=0;j<4;j++){
      const value=cells[j+1].textContent;
      if(j>i) assert.equal(value,'·');
      else {
        const weight=Number(value);
        assert.ok(weight>=0&&weight<=1);
        sum+=weight;
      }
    }
    assert.ok(Math.abs(sum-1)<.04);
  }
  assert.match(elements['attention-detail'].textContent,/Soma dos pesos permitidos = 1.0000/);
  const original = initial.children.slice(1,5).map(r=>r.children.map(c=>c.textContent));
  elements['attention-input'].value='ABCD123';
  elements['attention-input'].listeners.input();
  const extended=mat.children[0].children;
  for(let i=0;i<4;i++){
    for(let j=0;j<=i;j++)
      assert.equal(original[i][j+1],extended[i+1].children[j+1].textContent);
  }
  const focus=elements['attention-focus'];
  focus.value='2'; focus.listeners.input();
  assert.match(elements['attention-detail'].textContent,/Consulta 2/);
  assert.equal(mat.children[0].children[3].className,'attention-active');
  elements['attention-input'].value='';
  elements['attention-input'].listeners.input();
  assert.equal(mat.children.length,0);
  assert.match(elements['attention-stats'].textContent,/Digite algum texto/);
});

test('HEART_005 input and compute are bounded for long unicode strings', async () => {
  const {elements,context}=simulate('🦊'.repeat(120));
  vm.runInContext(await (await request('/heartai/tokenizer.js')).text(),context,{timeout:3000});
  vm.runInContext(await (await request('/heartai/attention.js')).text(),context,{timeout:3000});
  const table=elements['attention-matrix'].children[0];
  assert.ok(table.children.length<=15);
  assert.match(elements['attention-stats'].textContent,/Sequência truncada/);
  assert.match(elements['attention-detail'].textContent,/Vetor de saída/);
  const rows=table.children;
  for(let i=1;i<rows.length;i++){
    assert.equal(rows[i].children.length,rows.length);
    for(let j=i+1;j<rows.length;j++){
      assert.equal(rows[i].children[j].textContent,'·');
    }
  }
});
