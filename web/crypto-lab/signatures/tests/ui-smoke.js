"use strict";
// Preview-only UI smoke suite. Loaded after the real production scripts.
(async()=>{
const log=[];
const assert=(name,ok,data="")=>{log.push({name,ok:Boolean(ok),data});if(!ok)throw Error(name);};
const $=id=>document.getElementById(id);
const nap=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn,limit=15000){const start=Date.now();while(Date.now()-start<limit){if(fn())return;await nap(70);}throw Error("timeout: "+fn.toString().slice(0,50));}
try{
 await until(()=>$("wallets").querySelectorAll(".wallet").length===2 && $("status").textContent.includes("efêmeras"));
 assert("Two wallets rendered",$("wallets").querySelectorAll(".wallet").length===2);
 const balances=()=>[...document.querySelectorAll(".wallet .balance")].map(x=>parseInt(x.textContent,10));
 assert("Initial educational balances",balances().join(",")==="100,100");
 $("send").click();
 await until(()=>$("status").textContent.includes("Transferência educativa registrada"));
 assert("Transfer button works",document.querySelectorAll(".tx").length===1);
 assert("Signed transfer is verified",document.querySelectorAll(".tx:not(.invalid)").length===1);
 assert("Balances reflect transfer",balances().join(",")==="85,115");
 $("replay").click();
 await until(()=>$("status").textContent.includes("Replay detectado"));
 assert("Replay button rejects duplicate nonce",document.querySelectorAll(".tx.invalid").length===1);
 $("clear").click();
 await until(()=>$("status").textContent.includes("Histórico zerado"));
 assert("Ledger cleared",document.querySelectorAll(".tx").length===0);
 assert("Clear resets balances",balances().join(",")==="100,100");
 $("send").click();
 await until(()=>$("status").textContent.includes("Transferência educativa registrada"));
 $("tamper").click();
 await until(()=>$("status").textContent.includes("adulteração"));
 assert("Tampering button shows invalid signature",document.querySelectorAll(".tx.invalid").length===1);
 $("clear").click();await until(()=>$("status").textContent.includes("Histórico zerado"));
 $("amount").value="101";$("send").click();
 await until(()=>$("status").textContent.includes("Valor inteiro permitido"));
 assert("Invalid amount rejected",document.querySelectorAll(".tx").length===0);
}catch(e){log.push({name:"UNHANDLED",ok:false,data:String(e)})}
const pre=document.createElement("pre");pre.id="done";pre.textContent=JSON.stringify(log);document.body.append(pre);
})();
