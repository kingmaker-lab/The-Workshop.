// Run: node --test web/crypto-lab/signatures/tests/protocol.test.cjs
const test=require("node:test");
const assert=require("node:assert/strict");
const crypto=require("node:crypto").webcrypto;
if(!globalThis.crypto)globalThis.crypto=crypto;
const api=require("../protocol.js");
async function pair(){return Promise.all([api.makeWallet(),api.makeWallet()]);}
test("ECDSA P-256: wallets have distinct address, private key is nonextractable",async()=>{
 const [a,b]=await pair();
 assert.notEqual(a.address,b.address);
 assert.equal(a.address,await api.addressFromPublic(a.publicKey));
 assert.equal(a.privateKey.extractable,false);
 await assert.rejects(()=>crypto.subtle.exportKey("pkcs8",a.privateKey));
});
test("Valid signature updates fictitious balances and sequential nonce",async()=>{
 const [a,b]=await pair();
 const tx=await api.createTransaction(a,b.address,15,1);
 const state=await api.audit([tx],[a.address,b.address]);
 assert.equal(state.valid,true);
 assert.equal(state.balance[a.address],85);
 assert.equal(state.balance[b.address],115);
 assert.equal(state.nonce[a.address],1);
 const second=await api.createTransaction(a,b.address,5,2);
 assert.equal((await api.audit([tx,second],[a.address,b.address])).balance[a.address],80);
});
test("Changing the signed amount is caught by ECDSA verification",async()=>{
 const [a,b]=await pair();
 const tx=await api.createTransaction(a,b.address,7,1);
 const tampered={...tx,amount:9};
 const state=await api.audit([tampered],[a.address,b.address]);
 assert.equal(state.valid,false);
 assert.match(state.results[0].reason,/Assinatura/);
 assert.equal(state.balance[a.address],100);
});
test("Replay of a valid signed transaction is rejected",async()=>{
 const [a,b]=await pair();
 const tx=await api.createTransaction(a,b.address,10,1);
 const state=await api.audit([tx,{...tx}],[a.address,b.address]);
 assert.equal(state.valid,false);
 assert.equal(state.results[0].valid,true);
 assert.equal(state.results[1].valid,false);
 assert.match(state.results[1].reason,/Nonce/);
 assert.equal(state.balance[a.address],90);
});
test("Signed transfers cannot exceed educational balance",async()=>{
 const [a,b]=await pair();
 const tx=await api.createTransaction(a,b.address,101,1);
 const state=await api.audit([tx],[a.address,b.address]);
 assert.equal(state.valid,false);
 assert.match(state.results[0].reason,/Saldo/);
});
test("Sender identity is bound to public key and signature",async()=>{
 const [a,b]=await pair();
 const tx=await api.createTransaction(a,b.address,10,1);
 const forged={...tx,from:b.address,to:a.address};
 const state=await api.audit([forged],[a.address,b.address]);
 assert.equal(state.valid,false);
 assert.match(state.results[0].reason,/Chave pública/);
});
test("Validation rejects malformed transactions, self-transfers and zero amounts",async()=>{
 const [a,b]=await pair();
 const tx=await api.createTransaction(a,b.address,10,1);
 for(const forged of [{...tx,to:a.address},{...tx,amount:0},{...tx,nonce:0},{...tx,publicKey:"nonsense"}]){
  const state=await api.audit([forged],[a.address,b.address]);
  assert.equal(state.valid,false);
 }
});
