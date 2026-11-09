"use strict";
/* EXP-003 · Workshop educational signing protocol.
 * Domain-separated canonical payload; unsigned, fixed session allocations.
 * WebCrypto P-256 private keys are deliberately non-extractable.
 * Not a production cryptocurrency protocol or real identity system.
 */
(function (root) {
  const DOMAIN = "THE_WORKSHOP_EXP003_V1";
  const ALLOCATION = 100;
  const MAX_TX = 20;
  const utf8 = new TextEncoder();
  const hex = b => [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, "0")).join("");
  const base64 = b => btoa(String.fromCharCode(...new Uint8Array(b)));
  const unbase64 = s => Uint8Array.from(atob(s), c => c.charCodeAt(0));
  const subtle = () => root.crypto.subtle;
  async function sha256(v) { return hex(await subtle().digest("SHA-256", v)); }
  async function addressFromPublic(publicKeyBase64) {
    if (typeof publicKeyBase64 !== "string" || publicKeyBase64.length > 250) throw new Error("Chave pública inválida.");
    const bytes = unbase64(publicKeyBase64);
    if (bytes.byteLength < 60 || bytes.byteLength > 160) throw new Error("Tamanho da chave pública inválido.");
    return "wk_" + await sha256(bytes);
  }
  async function makeWallet() {
    const pair = await subtle().generateKey({name:"ECDSA",namedCurve:"P-256"}, false, ["sign","verify"]);
    const publicBytes = await subtle().exportKey("spki", pair.publicKey);
    const publicKey = base64(publicBytes);
    return {address:await addressFromPublic(publicKey), publicKey, privateKey:pair.privateKey};
  }
  // Explicit field ordering and stable types prevent ambiguous payload reserialization.
  function canonical(tx) {
    return JSON.stringify([DOMAIN,tx.from,tx.to,tx.amount,tx.nonce]);
  }
  async function createTransaction(wallet, to, amount, nonce) {
    if (!wallet || !wallet.privateKey || typeof to !== "string" ||
        !Number.isSafeInteger(amount) || amount <= 0 || !Number.isSafeInteger(nonce) || nonce < 1)
      throw new Error("Parâmetros inválidos para assinatura.");
    const tx = {from:wallet.address,to,amount,nonce,publicKey:wallet.publicKey};
    const signature = await subtle().sign({name:"ECDSA",hash:"SHA-256"},wallet.privateKey,utf8.encode(canonical(tx)));
    tx.signature = base64(signature);
    return tx;
  }
  // Validation always rebuilds balances and next nonces from fixed session allocations.
  // A malformed or fraudulent entry invalidates all subsequent records (no partial "valid ledger").
  async function audit(transactions, walletAddresses) {
    if (!Array.isArray(transactions)||!Array.isArray(walletAddresses)||walletAddresses.length!==2||
        new Set(walletAddresses).size!==2) throw new Error("Parâmetros do ledger inválidos.");
    const balance = Object.fromEntries(walletAddresses.map(addr=>[addr,ALLOCATION]));
    const nonce = Object.fromEntries(walletAddresses.map(addr=>[addr,0]));
    const results = [];
    let compromised=false;
    for (const tx of transactions.slice(0, MAX_TX + 1)) {
      let reason="";
      if (compromised) reason="Operação bloqueada após registro inválido.";
      else if (!tx || typeof tx!=="object" ||
               typeof tx.from!=="string" || typeof tx.to!=="string" ||
               typeof tx.publicKey!=="string" || typeof tx.signature!=="string" ||
               !Object.hasOwn(balance,tx.from) || !Object.hasOwn(balance,tx.to) ||
               tx.from===tx.to || !Number.isSafeInteger(tx.amount) || tx.amount<1 ||
               !Number.isSafeInteger(tx.nonce) || tx.nonce<1 || tx.publicKey.length>250 ||
               tx.signature.length>200) reason="Formato, remetente ou destinatário inválido.";
      else if (tx.nonce!==nonce[tx.from]+1) reason="Nonce incorreto: transação repetida ou fora de ordem.";
      else if (balance[tx.from]<tx.amount) reason="Saldo fictício insuficiente.";
      else {
        try {
          const addr = await addressFromPublic(tx.publicKey);
          if (addr!==tx.from) reason="Chave pública não corresponde ao remetente.";
          else {
            const key = await subtle().importKey("spki",unbase64(tx.publicKey),
              {name:"ECDSA",namedCurve:"P-256"},false,["verify"]);
            const valid = await subtle().verify({name:"ECDSA",hash:"SHA-256"},key,
              unbase64(tx.signature),utf8.encode(canonical(tx)));
            if (!valid) reason="Assinatura ECDSA não corresponde ao conteúdo.";
          }
        } catch (_) {reason="Falha na assinatura ou na chave pública.";}
      }
      const valid = !reason;
      results.push({tx, valid, reason:valid?"Assinatura, nonce e saldo válidos.":reason});
      if (valid) {
        balance[tx.from]-=tx.amount;
        balance[tx.to]+=tx.amount;
        nonce[tx.from]=tx.nonce;
      } else compromised=true;
    }
    if (transactions.length>MAX_TX) compromised=true;
    return {valid:!compromised, balance, nonce, results};
  }
  const api = Object.freeze({makeWallet,createTransaction,audit,addressFromPublic,canonical,ALLOCATION,MAX_TX,DOMAIN});
  root.WorkshopLedger = api;
  if (typeof module !== "undefined" && module.exports) module.exports=api;
})(globalThis);
