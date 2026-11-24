import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import worker from '../_worker.js';

const origin='https://workshop-labs.pages.dev';
const get=(path,method='GET')=>worker.fetch(new Request(origin+path,{method}));
const source=readFileSync(new URL('../argus/index.html',import.meta.url),'utf8');

test('ARGUS v0.5 additions are source mirrored without dropping historical content',async()=>{
 const response=await get('/argus/');
 assert.equal(response.status,200);
 assert.equal(await response.text(),source);
 assert.equal((await (await get('/argus/index.html')).text()),source);
 for(const id of ['visao','arquitetura','deteccoes','evidencia','telemetria',
  'executar','continuo','sigma','multihost','seguranca','roadmap']){
   assert.ok(source.includes('id="'+id+'"'),id);
 }
 for(const keyword of ['ARGUS v0.3 / CONTINUOUS INGEST','ARGUS v0.4 / SIGMA SUBSET',
  'ARGUS v0.5 / TEMPORAL CORRELATION','15 falhas em 30 segundos',
  '17','03','Navegação do ARGUS','python -m argus.main sigma-validate',
  'argus/config-v05-demo.yaml','multihost_auth_v05.jsonl',
  'multi_host_failed_auth_burst','estado de correlação e as baselines continuam em memória',
  'sigma.enabled: false','temporal_v05','enabled: false','50.000 linhas completas']){
  assert.ok(source.includes(keyword),keyword);
 }
 assert.ok(source.includes('href="#multihost"'));
});

test('ARGUS v0.5 display is static, no public ingestion or remote scripts',()=>{
 assert.doesNotMatch(source,/<script\b/i);
 assert.doesNotMatch(source,/<iframe\b/i);
 assert.doesNotMatch(source,/<form\b/i);
 assert.doesNotMatch(source,/<(?:img|script)[^>]+src\s*=\s*["']https?:/i);
 assert.ok(source.includes('não deve ser exposta à Internet'));
 assert.ok(source.includes('LOCAL'));
});

test('ARGUS v0.5 retains defensive headers, read-only verbs and 404',async()=>{
 const r=await get('/argus/');
 const csp=r.headers.get('content-security-policy');
 for(const req of ["default-src 'none'","script-src 'none'","connect-src 'none'",
  "frame-ancestors 'none'","object-src 'none'","base-uri 'none'"]){
  assert.ok(csp.includes(req),req);
 }
 assert.ok(csp.includes("style-src 'unsafe-inline'")); // existing inline CSS, not a new exception
 assert.equal(r.headers.get('x-content-type-options'),'nosniff');
 assert.equal(r.headers.get('x-frame-options'),'DENY');
 assert.equal(r.headers.get('cross-origin-opener-policy'),'same-origin');
 assert.equal(r.headers.get('cross-origin-resource-policy'),'same-origin');
 assert.equal(r.headers.get('referrer-policy'),'no-referrer');
 assert.ok(r.headers.get('strict-transport-security').includes('max-age='));
 assert.equal((await get('/argus/','HEAD')).status,200);
 assert.equal(await (await get('/argus/','HEAD')).text(),'');
 const post=await get('/argus/','POST');
 assert.equal(post.status,405);
 assert.equal(post.headers.get('allow'),'GET, HEAD');
 assert.equal((await get('/argus/not-found')).status,404);
});

test('NEXUS, HeartAI, Crypto, ARGUS and CERBERUS links remain available',async()=>{
 for(const path of ['/','/argus/','/heartai/','/nexus/','/nexus/exp009/',
  '/crypto-lab/','/crypto-lab/pow/','/crypto-lab/signatures/',
  '/crypto-lab/pow/miner.worker.js','/assets/labs.css']){
  assert.equal((await get(path)).status,200,path);
 }
 const home=await (await get('/')).text();
 for(const phrase of ['id="blockchain-experiments"','ARGUS PROJECT','CERBERUS PROTOCOL',
 'NEXUS-06 NEURAL LAB','HEARTAI / TOKENIZER']){
  assert.ok(home.includes(phrase),phrase);
 }
});
