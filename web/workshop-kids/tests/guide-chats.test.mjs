import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

const worker = fs.readFileSync(new URL("../worker.js",import.meta.url),"utf8")
  .replace(/export default \{ fetch\(request,env\)\{return respond\(request,env\);\} \};\s*$/,"");
const ctx = vm.createContext({Request,Response,URL,TextDecoder,Uint8Array,atob,addEventListener(){}});
vm.runInContext(worker,ctx,{timeout:8000});
const base="https://workshop-kids.test";
const get=path=>ctx.respond(new Request(base+path));
const html=n=>vm.runInContext(n,ctx);

test("Heart and Blade provide separate chat pages and APIs",async()=>{
 const heart=await get("/heart/").text();
 const blade=await get("/blade/conversar/").text();
 const home=await get("/").text();
 assert.match(home,/class="guide-card guide-heart"/);
 assert.match(home,/class="guide-card guide-blade"/);
 assert.match(heart,/href="\/blade\/conversar\/"/);
 assert.match(blade,/href="\/heart\/"/);
 assert.match(heart,/aria-current="page"/);
 assert.match(blade,/aria-current="page"/);
 assert.match(html("HEART_JS"),/fetch\("\/api\/heart"/);
 assert.match(html("BLADE_CHAT_JS"),/fetch\("\/api\/blade"/);
 assert.match(heart,/id="ai-consent"/);
 assert.match(blade,/id="blade-optin"/);
});
test("Blade chat uses new official art and red / black theme",async()=>{
 const blade=await get("/blade/conversar/").text();
 const css=await get("/blade/chat.css").text();
 assert.match(blade,/src="\/assets\/blade.webp\?v=e04bfb99"/);
 assert.match(blade,/alt="Blade, lobo netrunner/);
 assert.match(css,/background:#100b15/);
 assert.match(css,/#f3587a/);
 assert.doesNotMatch(css,/#f4f9fc|#dff4fc/);
 assert.equal(get("/assets/blade.webp?v=e04bfb99").status,200);
});
test("Both chats retain distinct safety boundaries",()=>{
 assert.match(get("/heart/").headers.get("Content-Security-Policy"),/connect-src 'self'/);
 assert.match(get("/blade/conversar/").headers.get("Content-Security-Policy"),/connect-src 'self'/);
 assert.match(get("/blade/").headers.get("Content-Security-Policy"),/script-src 'none'/);
 assert.match(html("BLADE_CHAT_HTML"),/workshop-news.pages.dev\/\#workshop/);
});
