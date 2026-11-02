import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

const source = fs.readFileSync(new URL("../worker.js",import.meta.url),"utf8")
  .replace(/export default \{ fetch\(request,env\)\{return respond\(request,env\);\} \};\s*$/,"");
const context=vm.createContext({Request,Response,URL,TextDecoder,Uint8Array,atob,addEventListener() {}});
vm.runInContext(source,context,{timeout:5000});
const url=path=>"https://workshop-kids.example"+path;
const request=(path,method="GET")=>context.respond(new Request(url(path),{method}));
const getText=(name)=>vm.runInContext(name,context);

test("Blade e Heart presentes nas três telas",async()=>{
 const home=await request("/").text();
 const game=await request("/jogar/").text();
 const chat=await request("/heart/").text();
 assert.match(home,/<img[^>]+src="\/assets\/blade.webp\?v=e04bfb99"[^>]+alt="Blade,/);
 assert.match(home,/<img[^>]+src="\/assets\/heart.webp\?v=00ff52e6"[^>]+alt="Heart,/);
 assert.match(game,/src="\/assets\/heart.webp\?v=00ff52e6"/);
 assert.match(chat,/src="\/assets\/heart.webp\?v=00ff52e6"/);
 assert.match(getText("GAME_JS"),/avatar\.src="\/assets\/heart.webp\?v=00ff52e6"/);
});
test("Sprites WebP são válidos, autocontidos e respondem a HEAD",async()=>{
 for(const name of ["blade","heart"]){
   const resource="/assets/"+name+".webp";
   const res=request(resource);
   assert.equal(res.status,200);
   assert.match(res.headers.get("Content-Type"),/image\/webp/);
   const bytes=Buffer.from(await res.arrayBuffer());
   assert.equal(bytes.toString("ascii",0,4),"RIFF");
   assert.equal(bytes.toString("ascii",8,12),"WEBP");
   assert.ok(bytes.length>20000);
   const head=request(resource,"HEAD");
   assert.equal(head.status,200);
   assert.equal((await head.arrayBuffer()).byteLength,0);
   assert.equal(request(resource,"POST").status,405);
 }
});
test("Imagens são permitidas pela CSP sem relaxar a segurança",()=>{
 for(const path of ["/","/jogar/","/heart/"]){
   const csp=request(path).headers.get("Content-Security-Policy");
   assert.match(csp,/img-src 'self'/);
   assert.match(csp,/frame-ancestors 'none'/);
   assert.match(csp,/object-src 'none'/);
 }
 assert.match(request("/heart/").headers.get("Content-Security-Policy"),/connect-src 'self'/);
 assert.match(request("/jogar/").headers.get("Content-Security-Policy"),/connect-src 'none'/);
});

test("Blade v2 mantém a arte completa e orienta para seção de responsáveis",async()=>{
 const home=await request("/").text();
 assert.match(home,/id="blade" aria-labelledby="blade-title"/);
 assert.match(home,/class="blade-showcase section"/);
 assert.match(home,/src="\/assets\/blade.webp\?v=e04bfb99"/);
 assert.match(home,/Guardião Digital|guardião digital/);
 assert.match(home,/href="#responsaveis"/);
 const css=await request("/styles.css").text();
 assert.match(css,/\.blade-poster img\{[^}]*object-fit:contain/);
});
