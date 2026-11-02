import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

const source=fs.readFileSync(new URL("../worker.js",import.meta.url),"utf8")
  .replace(/export default \{ fetch\(request,env\)\{return respond\(request,env\);\} \};\s*$/,"");
const ctx=vm.createContext({Request,Response,URL,TextDecoder,Uint8Array,atob,addEventListener() {}});
vm.runInContext(source,ctx,{timeout:6000});
const base="https://workshop-kids.test";
const serve=(path,method="GET")=>ctx.respond(new Request(base+path,{method}));
test("Blade tem página exclusiva, ligações internas e quatro quadros",async()=>{
 const p=serve("/blade/");
 assert.equal(p.status,200);
 assert.match(p.headers.get("Content-Type"),/text\/html/);
 const html=await p.text();
 assert.match(html,/<title>Blade \| Guardião Digital da Workshop Kids<\/title>/);
 assert.match(html,/src="\/assets\/blade.webp"/);
 assert.match(html,/id="quadrinho"/);
 assert.equal((html.match(/class="panel p[1-4]"/g)||[]).length,4);
 assert.match(html,/O clique misterioso/);
 assert.match(html,/senhas/i);
 assert.match(html,/adulto de confiança/i);
 assert.match(html,/https:\/\/workshop-news\.pages\.dev\/#workshop/);
 assert.doesNotMatch(html,/<script\b|<form\b/i);
 assert.equal(serve("/blade").status,200);
 assert.equal(serve("/blade/index.html").status,200);
 const home=await serve("/").text();
 assert.match(home,/href="\/blade\/"/);
 assert.match(home,/href="https:\/\/workshop-news\.pages\.dev\/#workshop"/);
});
test("Blade carrega apenas CSS de primeira parte e bloqueia execução JS",async()=>{
 const css=serve("/blade.css");
 assert.equal(css.status,200);
 assert.match(css.headers.get("Content-Type"),/text\/css/);
 assert.match(await css.text(),/\.comic-grid/);
 const csp=serve("/blade/").headers.get("Content-Security-Policy");
 assert.match(csp,/script-src 'none'/);
 assert.match(csp,/connect-src 'none'/);
 assert.match(csp,/img-src 'self'/);
 assert.match(csp,/frame-ancestors 'none'/);
 assert.equal(serve("/blade/","POST").status,405);
 const head=serve("/blade/","HEAD");
 assert.equal(head.status,200);
 assert.equal((await head.arrayBuffer()).byteLength,0);
});
test("Arte atualizada é WebP e permanece hospedada na própria origem",async()=>{
 const res=serve("/assets/blade.webp");
 assert.equal(res.status,200);
 const bytes=Buffer.from(await res.arrayBuffer());
 assert.equal(bytes.toString("ascii",0,4),"RIFF");
 assert.equal(bytes.toString("ascii",8,12),"WEBP");
 assert.ok(bytes.byteLength>=100000,"nova arte não pode ser uma miniatura indevida");
});
test("Heart, jogo e API continuam preservados",()=>{
 for(const p of ["/heart/","/jogar/","/heart.js","/game.js"])assert.equal(serve(p).status,200);
 const chatCsp=serve("/heart/").headers.get("Content-Security-Policy");
 assert.match(chatCsp,/connect-src 'self'/);
 assert.match(serve("/jogar/").headers.get("Content-Security-Policy"),/connect-src 'none'/);
});
