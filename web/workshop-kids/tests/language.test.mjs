// Node.js 22+ | node --test web/workshop-kids/tests/language.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import worker from '../worker.js';

const origin='https://workshop-kids.wolfpackworkshop.workers.dev';
async function ask(bot,band,message,aiOptIn=false,env={}){
  const request=new Request(origin+'/api/'+bot,{
    method:'POST',
    headers:{'Origin':origin,'Content-Type':'application/json'},
    body:JSON.stringify({band,message,aiOptIn})
  });
  const response=await worker.fetch(request,env);
  assert.equal(response.status,200);
  return response.json();
}

test('Heart adjusts robotic explanations to 4–6, 7–9 and 10–12',async()=>{
  const young=await ask('heart','4-6','Como funciona um robô?');
  const middle=await ask('heart','7-9','Como funciona um robô?');
  const older=await ask('heart','10-12','Como funciona um robô?');
  assert.match(young.reply,/Robôs são máquinas/);
  assert.match(middle.reply,/sensores/);
  assert.match(older.reply,/algoritmo/);
  assert.notEqual(young.reply,older.reply);
});

test('Blade adjusts cybersecurity vocabulary to age',async()=>{
  const young=await ask('blade','4-6','Como criar uma senha segura?');
  const middle=await ask('blade','7-9','Como criar uma senha segura?');
  const older=await ask('blade','10-12','Como criar uma senha segura?');
  assert.match(young.reply,/segredo/);
  assert.match(middle.reply,/longa/);
  assert.match(older.reply,/verificação em duas etapas/);
});

test('4–6 never invokes AI despite an opt-in flag',async()=>{
  const env={AI:{run(){throw Error('AI must never be invoked for ages 4–6')}}};
  const h=await ask('heart','4-6','Como funciona um robô?',true,env);
  const b=await ask('blade','4-6','Como criar uma senha segura?',true,env);
  assert.equal(h.mode,'guided');
  assert.equal(b.mode,'guided');
});

test('safety routing still recommends a trusted adult',async()=>{
  const h=await ask('heart','4-6','Quero me machucar');
  const b=await ask('blade','10-12','Quero me machucar');
  assert.match(h.reply,/adulto de confiança/);
  assert.match(b.reply,/adulto de confiança/);
});

test('personal details are not repeated in responses',async()=>{
  const b=await ask('blade','7-9','Meu telefone é 11999999999');
  assert.equal(b.category,'privacy');
  assert.doesNotMatch(b.reply,/11999999999/);
});

test('games are still routable',async()=>{
  const response=await worker.fetch(new Request(origin+'/jogos/'),{});
  assert.equal(response.status,200);
  assert.match(response.headers.get('content-type'),/text\/html/);
});
