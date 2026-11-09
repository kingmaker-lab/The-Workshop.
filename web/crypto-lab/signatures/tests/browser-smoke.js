"use strict";
// EXP-003 browser regression suite: intentionally served only by preview deployments.
(async () => {
  const log=[];
  const assert=(name,ok,data="")=>{log.push({name,ok:Boolean(ok),data});if(!ok)throw Error(name);};
  try {
    const L=globalThis.WorkshopLedger;
    assert("Secure context & Web Crypto",isSecureContext && !!crypto.subtle);
    const a=await L.makeWallet(), b=await L.makeWallet();
    assert("Unique wallet addresses",a.address!==b.address);
    assert("Non-exportable private key",a.privateKey.extractable===false);
    let leaked=false;try{await crypto.subtle.exportKey("pkcs8",a.privateKey);leaked=true;}catch(_){}
    assert("Private key export rejected",!leaked);
    assert("Address derivation",a.address===await L.addressFromPublic(a.publicKey));
    const tx=await L.createTransaction(a,b.address,15,1);
    const good=await L.audit([tx],[a.address,b.address]);
    assert("ECDSA signed transfer accepted",good.valid);
    assert("Balances 85 / 115",good.balance[a.address]===85&&good.balance[b.address]===115);
    assert("Nonce incremented to 1",good.nonce[a.address]===1);
    const tampered=await L.audit([{...tx,amount:16}],[a.address,b.address]);
    assert("Tampering detected",!tampered.valid&&tampered.results[0].reason.includes("Assinatura"));
    const replay=await L.audit([tx,{...tx}],[a.address,b.address]);
    assert("Replay rejected",!replay.valid&&replay.results[1].reason.includes("Nonce"));
    const overspend=await L.audit([await L.createTransaction(a,b.address,101,1)],[a.address,b.address]);
    assert("Insufficient balance rejected",!overspend.valid&&overspend.results[0].reason.includes("Saldo"));
    const forged=await L.audit([{...tx,from:b.address,to:a.address}],[a.address,b.address]);
    assert("Sender key binding",!forged.valid&&forged.results[0].reason.includes("Chave pública"));
    const second=await L.createTransaction(a,b.address,5,2);
    const next=await L.audit([tx,second],[a.address,b.address]);
    assert("Sequential nonce 2 works",next.valid&&next.balance[a.address]===80);
    const badZero=await L.audit([{...tx,amount:0}],[a.address,b.address]);
    assert("Zero amount rejected",!badZero.valid);
    const badSelf=await L.audit([{...tx,to:a.address}],[a.address,b.address]);
    assert("Self transfer rejected",!badSelf.valid);
  } catch (e) {log.push({name:"UNHANDLED",ok:false,data:String(e)});}
  const pre=document.createElement("pre");pre.id="done";pre.textContent=JSON.stringify(log);
  document.body.append(pre);
})();
