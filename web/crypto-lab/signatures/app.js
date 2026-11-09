"use strict";
(function () {
  const engine = globalThis.WorkshopLedger;
  const $ = id => document.getElementById(id);
  const wallets = [];
  const transactions = [];
  let working = false;
  const nice = addr => addr ? addr.slice(0,17)+"…"+addr.slice(-8) : "—";
  function status(msg) {$("status").textContent=msg;}
  function setWorking(on) {
    working=on;
    for (const id of ["send","verify","tamper","replay","clear","regen","sender","receiver","amount"]) $(id).disabled=on;
  }
  function pair(dl,label,value) {
    const dt=document.createElement("dt");dt.textContent=label;
    const dd=document.createElement("dd");dd.textContent=String(value);dl.append(dt,dd);
  }
  function showWallets(balance) {
    const root=$("wallets");root.replaceChildren();
    wallets.forEach((wallet,i)=>{
      const card=document.createElement("article");card.className="wallet";
      const title=document.createElement("h3");title.textContent="Carteira "+(i===0?"A":"B");
      const bal=document.createElement("p");bal.className="balance";
      bal.textContent=String(balance[wallet.address]);
      const unit=document.createElement("small");unit.textContent=" unidades fictícias";bal.append(unit);
      const key=document.createElement("p");key.className="address";
      key.textContent="Identificador: "+wallet.address;
      const note=document.createElement("p");note.textContent="ECDSA P-256 · chave privada não exportável";
      card.append(title,bal,key,note);root.append(card);
    });
  }
  async function repaint() {
    if(wallets.length!==2)return null;
    const audit=await engine.audit(transactions,wallets.map(w=>w.address));
    showWallets(audit.balance);
    const ledger=$("ledger");ledger.replaceChildren();
    if(!transactions.length) {
      const empty=document.createElement("p");empty.textContent="Nenhuma transação assinada. Saldo inicial: 100 unidades fictícias por carteira.";ledger.append(empty);
    }
    audit.results.forEach(({tx,valid,reason},idx)=>{
      const card=document.createElement("article");card.className="tx"+(valid?"":" invalid");
      const title=document.createElement("strong");title.textContent="Transação #"+(idx+1);
      const result=document.createElement("p");result.className="validation";
      result.textContent=(valid?"✓ ":"⚠ ")+reason;
      const dl=document.createElement("dl");
      pair(dl,"Origem",nice(tx.from));pair(dl,"Destino",nice(tx.to));
      pair(dl,"Quantidade",tx.amount);pair(dl,"Nonce",tx.nonce);
      const details=document.createElement("details");
      const summary=document.createElement("summary");summary.textContent="Inspecionar assinatura e chave pública";
      const code=document.createElement("code");
      code.textContent="Assinatura: "+tx.signature+"\nChave pública SPKI Base64: "+tx.publicKey+"\nPayload canônico: "+engine.canonical(tx);
      details.append(summary,code);
      card.append(title,result,dl,details);ledger.append(card);
    });
    return audit;
  }
  async function doAction(fn) {
    if(working)return;
    setWorking(true);
    try {await fn();}
    catch (_) {status("Falha ao executar a operação criptográfica. Verifique HTTPS e o navegador.");}
    finally {setWorking(false);}
  }
  async function regenerate() {
    wallets.length=0;transactions.length=0;
    status("Gerando pares ECDSA P-256 no navegador…");
    wallets.push(await engine.makeWallet());
    wallets.push(await engine.makeWallet());
    $("sender").value="0";$("receiver").value="1";
    await repaint();status("Duas carteiras efêmeras criadas. Faça uma transferência educativa.");
  }
  async function send() {
    const audit=await repaint();
    if(!audit.valid){status("Histórico inválido. Limpe o histórico antes de assinar novamente.");return;}
    if(transactions.length>=engine.MAX_TX){status("Limite educativo de 20 transferências.");return;}
    const from=Number($("sender").value),to=Number($("receiver").value),amount=Number($("amount").value);
    if(![0,1].includes(from)||![0,1].includes(to)||from===to){status("Selecione duas carteiras diferentes.");return;}
    if(!Number.isSafeInteger(amount)||amount<1||amount>100){status("Valor inteiro permitido: entre 1 e 100 unidades.");return;}
    if(audit.balance[wallets[from].address]<amount){status("Saldo fictício insuficiente.");return;}
    const tx=await engine.createTransaction(wallets[from],wallets[to].address,amount,audit.nonce[wallets[from].address]+1);
    transactions.push(tx);
    const after=await repaint();
    status(after.valid?"Assinatura conferida! Transferência educativa registrada.":"Falha na verificação da transação.");
  }
  $("sender").addEventListener("change",()=>{$("receiver").value=$("sender").value==="0"?"1":"0";});
  $("receiver").addEventListener("change",()=>{$("sender").value=$("receiver").value==="0"?"1":"0";});
  $("regen").addEventListener("click",()=>doAction(regenerate));
  $("send").addEventListener("click",()=>doAction(send));
  $("verify").addEventListener("click",()=>doAction(async()=>{const a=await repaint();status(a.valid?"Auditoria aprovada: assinaturas, saldos e nonces válidos.":"Auditoria reprovada: histórico adulterado ou com replay.");}));
  $("clear").addEventListener("click",()=>doAction(async()=>{transactions.length=0;await repaint();status("Histórico zerado. As duas carteiras e suas chaves continuam nesta sessão.");}));
  $("tamper").addEventListener("click",()=>doAction(async()=>{
    if(!transactions.length){status("Faça uma transferência antes de adulterar.");return;}
    transactions[transactions.length-1].amount+=1;
    const a=await repaint();
    status(!a.valid?"Valor alterado sem nova assinatura. A auditoria detectou a adulteração.":"Verifique o histórico.");
  }));
  $("replay").addEventListener("click",()=>doAction(async()=>{
    if(!transactions.length){status("Faça uma transferência antes de testar replay.");return;}
    if(transactions.length>=engine.MAX_TX){status("Limite de 20 registros.");return;}
    transactions.push({...transactions[transactions.length-1]});
    const a=await repaint();
    status(!a.valid?"Replay detectado: o nonce já foi utilizado.":"Verifique o histórico.");
  }));
  doAction(regenerate);
})();
