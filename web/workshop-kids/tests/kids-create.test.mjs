import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";
const source=fs.readFileSync(new URL("../worker.js",import.meta.url),"utf8")
 .replace(/export default \{ fetch\(request,env\)\{return respond\(request,env\);\} \};\s*$/,"");
const ctx=vm.createContext({Request,Response,URL,TextDecoder,Uint8Array,atob,addEventListener(){}});
vm.runInContext(source,ctx,{timeout:10000});
const constant=n=>vm.runInContext(n,ctx);
const serve=(p,method="GET")=>ctx.respond(new Request("https://workshop-kids.example"+p,{method}));
const client=constant("CREATE_JS");
const helpers=new Function(client.slice(0,client.indexOf("(()=>{"))+"; return {PIXEL_SIZE,COLOR_OPTIONS,buildStory,buildInvention,templateCells};")();
test("Kids Create substitui o placeholder e abre a oficina em rotas canônicas",async()=>{
 const home=await serve("/").text();
 assert.match(home,/href="\/criar\/"/);
 assert.doesNotMatch(home,/<h3>Kids Create<\/h3>[\s\S]*?<span class="soon">Em preparação<\/span>/);
 for(const p of ["/criar/","/criar","/criar/index.html","/create/","/create"]){
  const res=serve(p);assert.equal(res.status,200);
  const html=await res.text();
  assert.match(html,/id="pixel-board"/);
  assert.match(html,/id="story-text"/);
  assert.match(html,/id="invent-result"/);
  assert.match(html,/src="\/criar\/create.js" defer/);
  assert.match(html,/workshop-news.pages.dev\/#workshop/);
 }
});
test("Arquivos são da própria origem, sem rede ou persistência infantil",async()=>{
 for(const p of ["/criar/create.css","/criar/create.js"]){
  const res=serve(p);assert.equal(res.status,200);
  assert.match(res.headers.get("Content-Security-Policy"),/connect-src 'none'/);
  assert.equal(serve(p,"POST").status,405);
  assert.equal(serve(p,"HEAD").status,200);
 }
 assert.doesNotMatch(client,/\bfetch\s*\(|XMLHttpRequest|localStorage|sessionStorage|document\.cookie/);
 assert.doesNotThrow(()=>new Function(client));
});
test("Pixel Art possui grade de 256 pixels e dois modelos utilizáveis",()=>{
 assert.equal(helpers.PIXEL_SIZE,16);
 assert.equal(helpers.COLOR_OPTIONS.length,10);
 for(const shape of ["blank","heart","smile"]){
  const pixels=helpers.templateCells(shape);
  assert.equal(pixels.length,256);
  assert.ok(pixels.every(c=>/^#[a-f0-9]{6}$/i.test(c)));
  const colored=pixels.filter(c=>c!=="#ffffff").length;
  if(shape==="blank")assert.equal(colored,0);
  else assert.ok(colored>10);
 }
});
test("Histórias e invenções têm conteúdo editável e seguro",()=>{
 const story=helpers.buildStory("heart","forest","garden");
 assert.match(story,/a Heart, a lobinha exploradora/);
 assert.match(story,/floresta de estrelas/);
 assert.equal(helpers.buildStory("invalid","forest","garden"),"");
 const inv=helpers.buildInvention("organize","paper");
 assert.match(inv.text,/Organizar|organizar/);
 assert.match(inv.text,/papel e lápis/);
 assert.match(inv.text,/peça ajuda de um adulto/);
 assert.equal(helpers.buildInvention("invalid","paper"),null);
});
test("Chats, jogos e limites existentes estão preservados",()=>{
 for(const p of ["/heart/","/jogar/","/jogos/","/blade/","/blade/conversar/"])assert.equal(serve(p).status,200);
 assert.match(source,/KIDS_API_LIMITER/);
 assert.match(source,/KIDS_AI_LIMITER/);
 assert.match(constant("HEART_PROMPT"),/Você é a Heart, uma lobinha/);
});
