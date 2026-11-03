"use strict";
const encoder=new TextEncoder();
const $=id=>document.getElementById(id);
const chain=[];
async function hash(value){const digest=await crypto.subtle.digest("SHA-256",encoder.encode(value));return [...new Uint8Array(digest)].map(x=>x.toString(16).padStart(2,"0")).join("");}
async function fingerprint(b){return hash(JSON.stringify([b.index,b.previousHash,b.data]));}
async function render(){const area=$("chain");area.replaceChildren();let previous="0".repeat(64);let valid=true;
for(const b of chain){const actual=await fingerprint(b);const ok=b.previousHash===previous&&b.hash===actual;valid=valid&&ok;const card=document.createElement("article");card.className="block"+(ok?"":" bad");const title=document.createElement("strong");title.textContent="BLOCO #"+b.index+" "+(ok?"✓":"⚠ ALTERADO");card.append(title);for(const [k,v] of [["Dados",b.data],["Hash anterior",b.previousHash],["Hash registrado",b.hash],["Hash calculado",actual]]){const p=document.createElement("p");const label=document.createElement("b");label.textContent=k+": ";const value=document.createElement("span");value.className="hash";value.textContent=v;p.append(label,value);card.append(p);}area.append(card);previous=b.hash;}
$("status").textContent=valid?"Cadeia íntegra no modelo didático.":"Inconsistência detectada na cadeia."; }
async function add(data){const prev=chain.length?chain[chain.length-1].hash:"0".repeat(64);const b={index:chain.length,previousHash:prev,data};b.hash=await fingerprint(b);chain.push(b);await render();}
let busy=false;async function locked(fn){if(busy)return;busy=true;try{await fn();}catch(e){$("status").textContent="Não foi possível calcular o hash. Use HTTPS e um navegador moderno.";}finally{busy=false;}}
$("add").addEventListener("click",()=>locked(async()=>{if(chain.length>=12){$("status").textContent="Limite didático de 12 blocos.";return;}await add($("payload").value.trim()||"(vazio)");}));
$("tamper").addEventListener("click",()=>locked(async()=>{if(chain.length<2){$("status").textContent="Adicione um bloco antes de adulterar.";return;}chain[1].data+=" [ALTERADO]";await render();}));
$("reset").addEventListener("click",()=>locked(async()=>{chain.length=0;await add("Genesis");}));
locked(()=>add("Genesis"));
