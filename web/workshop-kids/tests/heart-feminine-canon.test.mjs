import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

const source=fs.readFileSync(new URL("../worker.js",import.meta.url),"utf8")
  .replace(/export default \{ fetch\(request,env\)\{return respond\(request,env\);\} \};\s*$/,"");
const context=vm.createContext({Request,Response,URL,TextDecoder,Uint8Array,atob,addEventListener(){}});
vm.runInContext(source,context,{timeout:8000});
const constant=name=>vm.runInContext(name,context);
const get=path=>context.respond(new Request("https://workshop-kids.test"+path));

test("Heart é sempre apresentada no feminino em páginas, jogo e chat",async()=>{
  const targets=[
    constant("HTML"),constant("GAME_HTML"),constant("GAME_JS"),constant("HEART_HTML"),constant("HEART_JS")
  ];
  for(const text of targets){
    assert.doesNotMatch(text,/\b(?:o|O|do|ao) Heart\b/);
    assert.doesNotMatch(text,/\b(?:o|um|nosso) lobinho\b/);
  }
  assert.match(await get("/").text(),/Conheça a Heart e o Blade/);
  assert.match(await get("/heart/").text(),/Conversar com a Heart/);
  assert.match(await get("/jogar/").text(),/A Heart e a Missão dos Algoritmos/);
});
test("Identidade da Heart é feminina também nas respostas e instruções de IA",()=>{
  const prompt=constant("HEART_PROMPT");
  assert.match(prompt,/Você é a Heart, uma lobinha virtual/);
  assert.match(prompt,/assistente EDUCATIVA/);
  assert.match(prompt,/Nunca peça nome/);
  assert.match(prompt,/Não gere URLs/);
  const guided=vm.runInContext("HeartGuided.answer('Quem é você?')",context);
  const greeting=vm.runInContext("HeartGuided.answer('oi')",context);
  assert.match(guided.reply,/Eu sou a Heart, uma lobinha virtual/);
  assert.match(greeting.reply,/Eu sou a Heart, sua guia/);
  assert.equal(guided.mode,"guided");
});
test("Imagens oficiais atuais são usadas em todas as telas e avatares",async()=>{
  const heartVersion="/assets/heart.webp?v=00ff52e6",bladeVersion="/assets/blade.webp?v=e04bfb99";
  for(const name of ["HTML","GAME_HTML","HEART_HTML"]){
    assert.match(constant(name),/\/assets\/heart.webp\?v=00ff52e6/);
  }
  for(const name of ["HTML","BLADE_HTML","BLADE_CHAT_HTML"]){
    assert.match(constant(name),/\/assets\/blade.webp\?v=e04bfb99/);
  }
  assert.match(constant("GAME_JS"),/avatar\.src="\/assets\/heart.webp\?v=00ff52e6"/);
  for(const path of [heartVersion,bladeVersion]){
    const response=get(path);
    assert.equal(response.status,200);
    assert.equal(response.headers.get("Content-Type"),"image/webp");
    const bytes=Buffer.from(await response.arrayBuffer());
    assert.equal(bytes.toString("ascii",0,4),"RIFF");
    assert.equal(bytes.toString("ascii",8,12),"WEBP");
  }
});
test("Os chats e a segurança da aplicação permanecem separados",()=>{
  assert.match(constant("HEART_JS"),/fetch\("\/api\/heart"/);
  assert.match(constant("BLADE_CHAT_JS"),/fetch\("\/api\/blade"/);
  assert.match(constant("HEART_HTML"),/id="ai-consent"/);
  assert.match(constant("BLADE_CHAT_HTML"),/id="blade-optin"/);
  assert.match(get("/heart/").headers.get("Content-Security-Policy"),/connect-src 'self'/);
  assert.match(get("/blade/conversar/").headers.get("Content-Security-Policy"),/connect-src 'self'/);
});
