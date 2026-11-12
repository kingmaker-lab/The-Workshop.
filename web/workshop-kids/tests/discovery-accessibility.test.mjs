import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

const src=fs.readFileSync(new URL("../worker.js",import.meta.url),"utf8").replace(/export default \{ fetch\(request,env\)\{return respond\(request,env\);\} \};\s*$/,"");
const ctx=vm.createContext({Request,Response,URL,TextDecoder,Uint8Array,atob,addEventListener(){}});
vm.runInContext(src,ctx,{timeout:15000});
const constant=name=>vm.runInContext(name,ctx);
const page=(path,method="GET")=>ctx.respond(new Request("https://workshop-kids.test"+path,{method}));
const js=constant("KIDS_DISCOVERY_JS");
const filterSource=js.split("/* FILTER UI */")[0];
const {kidsCatalogMatches}=new Function(filterSource+"; return {kidsCatalogMatches}")();

test("Catálogo organiza cinco aventuras sem exigir dados pessoais",async()=>{
 const res=page("/jogos/");
 const html=await res.text();
 assert.equal(res.status,200);
 assert.equal((html.match(/class="catalog-card/g)||[]).length,5);
 assert.match(html,/id="filtros"/);
 assert.match(html,/data-filter-age="4-6"/);
 assert.match(html,/data-filter-age="7-9"/);
 assert.match(html,/data-filter-age="10-12"/);
 assert.match(html,/data-filter-topic="programming"/);
 assert.match(html,/data-filter-topic="safety"/);
 assert.match(html,/data-filter-topic="science"/);
 assert.match(html,/id="catalog-count" role="status" aria-live="polite"/);
 assert.match(html,/id="catalog-empty"[^>]*hidden/);
 assert.match(html,/href="\/#jogar"/);
 assert.match(html,/href="https:\/\/workshop-news.pages.dev\/#workshop"/);
 assert.match(html,/id="reading-toggle"[^>]*aria-pressed="false"/);
});
test("Filtro funciona sem rastreamento ou armazenamento",()=>{
 assert.equal(kidsCatalogMatches({ages:"4-6 7-9",topic:"programming"},"4-6","programming"),true);
 assert.equal(kidsCatalogMatches({ages:"7-9 10-12",topic:"science"},"4-6","science"),false);
 assert.equal(kidsCatalogMatches({ages:"7-9 10-12",topic:"safety"},"7-9","safety"),true);
 assert.equal(kidsCatalogMatches({ages:"7-9 10-12",topic:"safety"},"10-12","science"),false);
 assert.equal(kidsCatalogMatches({ages:"7-9 10-12",topic:"science"},"all","all"),true);
 for(const s of [js,constant("KIDS_ACCESS_JS")]){
  assert.doesNotMatch(s,/\bfetch\s*\(|localStorage|sessionStorage|document\.cookie|XMLHttpRequest/);
  assert.doesNotThrow(()=>new Function(s));
 }
});
test("Modo leitura é acessível nos três jogos e funciona sem persistência",async()=>{
 for(const path of ["/jogos/robot-factory/","/jogos/cyber-guardian/","/jogos/mini-circuit/"]){
  const html=await page(path).text();
  assert.match(html,/id="reading-toggle"/);
  assert.match(html,/src="\/jogos\/access.js" defer/);
  assert.match(html,/role="status"/);
 }
 const css=await page("/jogos/games.css").text();
 assert.match(css,/body\.reading-mode/);
 assert.match(css,/\.catalog-card\[hidden\]/);
 for(const path of ["/jogos/access.js","/jogos/discovery.js"]){
  const response=page(path);
  assert.equal(response.status,200);
  assert.match(response.headers.get("Content-Type"),/application\/javascript/);
  assert.match(response.headers.get("Content-Security-Policy"),/connect-src 'none'/);
  assert.equal(page(path,"POST").status,405);
 }
});
test("Versões oficiais e rotas existentes permanecem intactas",()=>{
 for(const path of ["/","/jogar/","/heart/","/blade/","/blade/conversar/","/api/heart","/api/blade"]){
  assert.ok(src.includes(path),"route retained: "+path);
 }
 assert.match(src,/KIDS_AI_LIMITER/);
 assert.match(src,/KIDS_API_LIMITER/);
 assert.match(constant("KIDS_GAMES_HTML"),/heart.webp\?v=00ff52e6/);
 assert.match(constant("KIDS_GAMES_HTML"),/blade.webp\?v=e04bfb99/);
});
