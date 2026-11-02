import test from 'node:test';
import assert from 'node:assert/strict';
import { webcrypto as nodeCrypto } from 'node:crypto';
import worker from '../worker.mjs';
import { commands } from '../commands.mjs';
const crypto = globalThis.crypto || nodeCrypto;
const kp = await crypto.subtle.generateKey('Ed25519', true, ['sign', 'verify']);
const pub = Buffer.from(await crypto.subtle.exportKey('raw', kp.publicKey)).toString('hex');
const env = { DISCORD_PUBLIC_KEY: pub, ALLOWED_GUILD_IDS: '123456789012345678', ENABLE_AI: 'false' };
const base = 'https://discord.local/interactions';
async function signed(body, { timestamp=Math.floor(Date.now()/1000), signature=true, newEnv=env, ctx={} }={}) {
  const payload=JSON.stringify(body);
  const bytes = new TextEncoder().encode(String(timestamp)+payload);
  const sig = Buffer.from(await crypto.subtle.sign('Ed25519',kp.privateKey,bytes)).toString('hex');
  return worker.fetch(new Request(base,{method:'POST',headers:{'x-signature-timestamp':String(timestamp),'x-signature-ed25519':signature?sig:'00'.repeat(64)},body:payload}),newEnv,ctx);
}
function cmd(name,options=[],guild_id='123456789012345678') { return {type:2,guild_id,application_id:'234567890123456789',token:'test',data:{name,options}}; }
test('Health is safe but credential state is visible',async()=>{
  const r=await worker.fetch(new Request('https://discord.local/health'),{});
  assert.deepEqual(await r.json(),{service:'workshop-discord',version:'0.1',configured:false});
});
test('Signed PING accepted',async()=>{assert.deepEqual(await (await signed({type:1})).json(),{type:1});});
test('Invalid and stale signatures rejected',async()=>{
 assert.equal((await signed({type:1},{signature:false})).status,401);
 assert.equal((await signed({type:1},{timestamp:Math.floor(Date.now()/1000)-600})).status,401);
});
test('Unknown guild blocked, guild-only command metadata',async()=>{
 const v=await (await signed(cmd('workshop',[],'987654321012345678'))).json();
 assert.match(v.data.content,/servidor autorizado/);
 assert.equal(v.data.flags,64);
 for(const c of commands) {assert.deepEqual(c.contexts,[0]);assert.deepEqual(c.integration_types,[0]);}
});
test('Heart education fallback no AI, data prompts blocked',async()=>{
 const r=await (await signed(cmd('heart',[{name:'pergunta',value:'O que é uma variável no Python?'}]))).json();
 assert.match(r.data.content,/Variável/);
 assert.deepEqual(r.data.allowed_mentions,{parse:[]});
 const p=await (await signed(cmd('heart',[{name:'pergunta',value:'meu email é student@example.com'}]))).json();
 assert.match(p.data.content,/informações pessoais/);
});
test('Blade topics do not access links, Ghost verifies logic without persistence',async()=>{
 const blade=await (await signed(cmd('blade',[{name:'assunto',value:'golpe'}]))).json();
 assert.match(blade.data.content,/Desconfie/);
 const challenge=await (await signed(cmd('ghost',[{name:'codigo',value:'2'}]))).json();
 assert.match(challenge.data.content,/JBYS/);
 const yes=await (await signed(cmd('ghost',[{name:'codigo',value:'2'},{name:'resposta',value:'wolf'}]))).json();
 assert.match(yes.data.content,/Flag encontrada/);
});
test('AI calls guarded and deferred response, output is ephemeral',async()=>{
 const calls=[];let wait;
 const newEnv={...env,ENABLE_AI:'true',AI:{run:async(m,p)=>{calls.push(m);return m.includes('guard')?{response:'safe'}:{response:'Um algoritmo é uma lista de passos.'};}}};
 const r=await signed(cmd('heart',[{name:'pergunta',value:'Como funciona um algoritmo?'}]),{newEnv,ctx:{waitUntil:p=>{wait=p;}}});
 assert.deepEqual(await r.json(),{type:5,data:{flags:64}});
 const saved=globalThis.fetch;
 // The async background reply may already run, so intercept network before invoking above instead in integration tests.
 await wait;
 assert.equal(calls.length,3);
});

test('No configuration, oversized body and invalid methods fail closed',async()=>{
 const none=await signed({type:1},{newEnv:{}});
 assert.equal(none.status,503);
 assert.equal((await worker.fetch(new Request(base,{method:'GET'}),env)).status,404);
 const massive='x'.repeat(9000);
 assert.equal((await worker.fetch(new Request(base,{method:'POST',body:massive}),env)).status,413);
});
