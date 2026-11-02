import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

const original=fs.readFileSync(new URL("../worker.js",import.meta.url),"utf8");
const source=original.replace(/export default \{ fetch\(request,env\)\{return respond\(request,env\);\} \};\s*$/,"");
const context=vm.createContext({Request,Response,URL,TextDecoder,addEventListener(){}});
vm.runInContext(source,context,{timeout:5000});
const site="https://workshop-kids.example";
function post(message,band="10-12",headers={},body){
 return context.respond(new Request(site+"/api/heart",{method:"POST",headers:{Origin:site,"Content-Type":"application/json",...headers},body:body===undefined?JSON.stringify({message,band}):body}),{AI:{run:async()=>({response:"safe"})}});
}
test("Heart chat integrated with landing and games intact",async()=>{
 const home=await context.respond(new Request(site+"/")).text();
 assert.match(home,/href="\/heart\/"/);
 assert.match(home,/href="\/jogar\/"/);
 const chat=context.respond(new Request(site+"/heart/"));
 assert.equal(chat.status,200);
 assert.match(chat.headers.get("Content-Security-Policy"),/connect-src 'self'/);
 assert.match(await chat.text(),/Conversar com Heart/);
 for(const route of ["/heart.js","/heart.css","/jogar/","/game.js"]){
  assert.equal(context.respond(new Request(site+route)).status,200);
 }
});
test("Younger children stay guided, without inference",async()=>{
 let calls=0;const env={AI:{run:async()=>{calls++;throw Error("should not call AI");}}};
 const req=new Request(site+"/api/heart",{method:"POST",headers:{"Origin":site,"Content-Type":"application/json"},body:JSON.stringify({message:"Quero aprender sobre planetas",band:"4-6"})});
 const res=await context.respond(req,env);const reply=await res.json();
 assert.equal(res.status,200);assert.equal(calls,0);assert.equal(reply.mode,"guided");
});
test("Moderated AI answers limited educational topics for Inventores/Criadores",async()=>{
 const models=[];
 const env={AI:{run:async(model,payload)=>{
  models.push({model,roles:payload.messages.map(m=>m.role)});
  return model.includes("guard")?{response:"safe"}:{response:"Robôs percebem o ambiente com sensores e usam instruções para agir. 🤖"};
 }}};
 const req=new Request(site+"/api/heart",{method:"POST",headers:{"Origin":site,"Content-Type":"application/json","CF-Connecting-IP":"198.51.100.40"},body:JSON.stringify({message:"Como um robô usa sensores?",band:"7-9",aiOptIn:true})});
 const res=await context.respond(req,env);
 assert.equal(res.status,200);
 assert.equal((await res.json()).mode,"ai");
 assert.equal(models.length,3);
 assert.match(models[0].model,/guard/);
 assert.match(models[1].model,/llama-3\.2/);
 assert.match(models[2].model,/guard/);
});
test("No inference on privacy, danger or unrelated content",async()=>{
 let calls=0;const env={AI:{run:async()=>{calls++;throw Error("must not call");}}};
 for(const message of ["meu telefone 11999999999","eu quero morrer","meu email e kid@example.com","qual o melhor celular para mim?"]){
  const req=new Request(site+"/api/heart",{method:"POST",headers:{"Origin":site,"Content-Type":"application/json"},body:JSON.stringify({message,band:"10-12"})});
  const res=await context.respond(req,env);
  assert.equal(res.status,200);
  assert.equal((await res.json()).mode,"guided");
 }
 assert.equal(calls,0);
});
test("Cross-site requests, oversized JSON and extra roles are rejected",async()=>{
 assert.equal((await post("oi","10-12",{Origin:"https://another.example"})).status,403);
 assert.equal((await post("oi","10-12",{},JSON.stringify({message:"oi",band:"10-12",role:"system"}))).status,400);
 assert.equal((await post("oi","10-12",{},JSON.stringify({message:"x".repeat(2000),band:"10-12"}))).status,413);
 assert.equal((await post("oi","10-12",{"Content-Type":"text/plain"})).status,415);
});
test("Guard fails closed with curated fallback",async()=>{
 const env={AI:{run:async()=>({response:"unsafe\nS9"})}};
 const req=new Request(site+"/api/heart",{method:"POST",headers:{Origin:site,"Content-Type":"application/json","CF-Connecting-IP":"198.51.100.41"},body:JSON.stringify({message:"Como um robô usa sensores?",band:"10-12",aiOptIn:true})});
 const res=await context.respond(req,env); const reply=await res.json();
 assert.equal(res.status,200);
 assert.equal(reply.mode,"guided");
 assert.equal(reply.category,"safety");
});

test("No adult opt-in means no model call",async()=>{
 let calls=0;
 const env={AI:{run:async()=>{calls++;return {response:"safe"};}}};
 const req=new Request(site+"/api/heart",{method:"POST",headers:{Origin:site,"Content-Type":"application/json"},body:JSON.stringify({message:"Como um robô usa sensores?",band:"10-12",aiOptIn:false})});
 const res=await context.respond(req,env); const value=await res.json();
 assert.equal(value.mode,"guided");
 assert.equal(calls,0);
});
