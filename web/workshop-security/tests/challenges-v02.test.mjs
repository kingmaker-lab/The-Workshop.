import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import vm from 'node:vm';
import {TextEncoder} from 'node:util';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const code=await readFile(path.join(root,'worker.mjs'),'utf8');
const start=code.indexOf('const ENC=new TextEncoder();');
const end=code.indexOf('function missionMeta(');
assert.ok(start>=0&&end>start,'Mission section exists');
const ctx={TextEncoder,Uint8Array,crypto:globalThis.crypto,btoa:globalThis.btoa,atob:globalThis.atob};
const {MISSIONS,puzzle}=vm.runInNewContext(code.slice(start,end)+'\n({MISSIONS,puzzle})',ctx);
const flags=['WS{1234567890ABCDEF12}','WS{FFFFFFFFFFFFFFFFFF}','WS{001122334455667788}'];
const rot13=s=>s.replace(/[A-Za-z]/g,c=>String.fromCharCode(c.charCodeAt(0)+(c.toLowerCase()<='m'?13:-13)));
function decode(id,raw){
 switch(id){
 case 'base64':return atob(raw);
 case 'rot13':return rot13(raw);
 case 'html':return raw.match(/data-flag="([^"]+)"/)[1];
 case 'logs':return raw.match(/X-Workshop-Flag: (WS\{[A-F0-9]+\})/)[1];
 case 'xor':return raw.trim().split(/\s+/).map(s=>String.fromCharCode(parseInt(s,16)^0x23)).join('');
 case 'js':return String.fromCharCode(...raw.match(/const codes = \[([0-9,\s]+)\]/)[1].split(',').map(Number));
 case 'json':return atob(JSON.parse(raw).incident.evidence.payload.split('').reverse().join(''));
 case 'bits':return raw.split(/\s+/).map(b=>String.fromCharCode(parseInt(b,2))).join('');
 case 'url':return decodeURIComponent(raw);
 case 'tcp':return JSON.parse(raw).filter(x=>x.flow==='LAB-01').sort((a,b)=>a.seq-b.seq).map(x=>x.data).join('');
 case 'sql':return [...raw.matchAll(/\((\d+),'([^']+)'\)/g)].sort((a,b)=>Number(a[1])-Number(b[1])).map(x=>x[2]).join('');
 case 'regex':return raw.split('\n').filter(x=>x.includes('action=allow role=analyst source=simulated')).map(x=>x.split('evidence=')[1])[0];
 case 'dns':return [...raw.matchAll(/_part(\d+) IN TXT "([^"]+)"/g)].sort((a,b)=>Number(a[1])-Number(b[1])).map(x=>x[2]).join('');
 case 'python':return raw.match(/masked = \[([0-9,\s]+)\]/)[1].split(',').map(Number).reverse().map(n=>String.fromCharCode(n^0x17)).join('');
 case 'camadas':return [...rot13(atob(raw))].reverse().join('');
 default:throw Error('Unknown mission '+id);
 }
}
test('catalog has 15 stable IDs and 1855 possible points',()=>{
 assert.equal(MISSIONS.length,15);
 assert.equal(new Set(MISSIONS.map(x=>x.id)).size,15);
 for(const id of ['base64','rot13','html','logs','xor','js','json'])assert.ok(MISSIONS.some(m=>m.id===id));
 assert.equal(MISSIONS.reduce((n,x)=>n+x.points,0),1855);
});
test('all artifacts reconstruct the unique per-player flag',()=>{
 for(const expected of flags)for(const mission of MISSIONS){
  const artifact=puzzle(mission.id,expected);
  assert.ok(artifact?.file&&artifact?.instruction&&artifact?.content,mission.id);
  assert.equal(decode(mission.id,artifact.content),expected,mission.id);
 }
});
test('filtering, Argus, Oni and dynamic counters survive',async()=>{
 const html=await readFile(path.join(root,'index.html'),'utf8');
 const app=await readFile(path.join(root,'app.js'),'utf8');
 for(const marker of ['id="missionFilters"','id="statPoints"','id="argus"','class="host-card"','id="rankRows"'])assert.ok(html.includes(marker),marker);
 assert.match(app,/state\.missions\.filter/);
 assert.match(app,/state\.missions\.reduce\(\(sum,c\)=>sum\+c\.points,0\)/);
 assert.ok(!app.includes("' / 07'"));
});
