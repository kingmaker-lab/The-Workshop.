"use strict";
const ZERO = "0".repeat(64);
const encoder = new TextEncoder();
const $ = (id) => document.getElementById(id);
const chain = [];
let worker = null;
const asHex = (bytes) => Array.from(new Uint8Array(bytes), v => v.toString(16).padStart(2, "0")).join("");
async function sha256(input) { return asHex(await crypto.subtle.digest("SHA-256", encoder.encode(input))); }
function blockPayload(b) { return JSON.stringify([b.index, b.previousHash, b.data, b.difficulty, b.nonce]); }
const number = (n) => new Intl.NumberFormat("pt-BR", { maximumFractionDigits:0 }).format(n);
const seconds = (n) => new Intl.NumberFormat("pt-BR", { maximumFractionDigits:1, minimumFractionDigits:1 }).format(n/1000) + " s";
function status(message) { $("status").textContent = message; }
function metrics(attempts, elapsedMs) {
  $("attempts").textContent = number(attempts);
  $("elapsed").textContent = seconds(elapsedMs);
  $("rate").textContent = number(elapsedMs > 0 ? attempts / (elapsedMs/1000) : 0) + " H/s";
}
function busy(on) {
  for (const id of ["mine", "verify", "tamper", "reset"]) $(id).disabled = on;
  $("cancel").disabled = !on;
  $("payload").disabled = on;
  $("difficulty").disabled = on;
}
async function inspect() {
  let parentHash = ZERO;
  const records = [];
  for (const b of chain) {
    const recalculated = await sha256(blockPayload(b));
    const linked = b.previousHash === parentHash;
    const hashed = b.hash === recalculated;
    const difficultyOK = b.index === 0 ? b.difficulty === 0 && b.nonce === 0 :
      Number.isInteger(b.difficulty) && b.difficulty >= 1 && b.difficulty <= 4 &&
      Number.isInteger(b.nonce) && b.nonce >= 0 && b.nonce < 500000 && recalculated.startsWith("0".repeat(b.difficulty));
    const indexOK = b.index === records.length;
    const valid = linked && hashed && difficultyOK && indexOK;
    records.push({block:b, recalculated, valid});
    parentHash = b.hash;
  }
  return records;
}
function addPair(dl, label, value) {
  const dt = document.createElement("dt");
  dt.textContent = label;
  const dd = document.createElement("dd");
  dd.textContent = String(value);
  dl.append(dt, dd);
}
async function render() {
  const checks = await inspect();
  const root = $("chain");
  root.replaceChildren();
  for (const {block:b, recalculated, valid} of checks) {
    const el = document.createElement("article");
    el.className = "block " + (valid ? "good" : "bad");
    const head = document.createElement("strong");
    head.textContent = "BLOCO #" + b.index + (b.index === 0 ? " · GÊNESE" : " · PROOF-OF-WORK");
    const result = document.createElement("p");
    result.className = "result";
    result.textContent = valid ? "✓ Hash, índice, dificuldade e ligação válidos" : "⚠ Integridade ou Proof-of-Work inválido";
    const dl = document.createElement("dl");
    addPair(dl, "Dados", b.data);
    addPair(dl, "Anterior", b.previousHash);
    addPair(dl, "Dificuldade", b.difficulty + " zero(s) hexadecimais");
    addPair(dl, "Nonce", b.nonce);
    addPair(dl, "Hash gravado", b.hash);
    addPair(dl, "SHA-256 atual", recalculated);
    el.append(head, result, dl);
    root.append(el);
  }
  return checks.every(x => x.valid);
}
async function reset() {
  if (worker) { worker.terminate(); worker = null; }
  busy(false);
  chain.length = 0;
  const genesis = {index:0, previousHash:ZERO, data:"Genesis", difficulty:0, nonce:0};
  genesis.hash = await sha256(blockPayload(genesis));
  chain.push(genesis);
  metrics(0,0);
  await render();
  status("Bloco gênese criado. Escolha a dificuldade e inicie a mineração.");
}
async function mine() {
  if (worker) return;
  if (chain.length > 5) { status("Limite educativo: até 5 blocos minerados. Reinicie a cadeia."); return; }
  if (!(await render())) { status("Cadeia adulterada. Reinicie para continuar a mineração."); return; }
  const data = $("payload").value.slice(0,140);
  const difficulty = Number($("difficulty").value);
  const previous = chain[chain.length-1];
  const task = {type:"mine", index:chain.length, data, difficulty, previousHash:previous.hash};
  let w;
  try { w = new Worker("./miner.worker.js"); }
  catch (_) { status("Não foi possível iniciar o Worker. Use HTTPS ou localhost."); return; }
  worker = w;
  busy(true);
  metrics(0,0);
  status("Buscando nonce válido. Você pode cancelar a qualquer momento.");
  w.onmessage = async (event) => {
    if (w !== worker) return;
    const r = event.data || {};
    if (r.type === "progress") { metrics(r.attempts,r.elapsedMs); return; }
    w.terminate(); worker = null; busy(false);
    if (r.attempts !== undefined) metrics(r.attempts,r.elapsedMs);
    if (r.type === "found") {
      const candidate = r.block;
      const expected = await sha256(blockPayload(candidate));
      if (candidate.hash !== expected || !expected.startsWith("0".repeat(candidate.difficulty)) || candidate.previousHash !== previous.hash) {
        status("Resultado rejeitado na verificação independente."); return;
      }
      chain.push(candidate);
      const ok = await render();
      status(ok ? "Bloco #" + candidate.index + " minerado e verificado! Nonce: " + number(candidate.nonce) + "." : "Bloco não passou na validação!");
    } else if (r.type === "exhausted") {
      status("Limite de 500.000 tentativas atingido sem solução. Reduza a dificuldade ou tente novamente.");
    } else { status(r.message || "Falha no processo de mineração."); }
  };
  w.onerror = () => { if(w !== worker)return;w.terminate();worker=null;busy(false);status("Erro ao executar a mineração local."); };
}
$("mine").addEventListener("click", () => { mine().catch(() => status("Erro durante a mineração.")); });
$("cancel").addEventListener("click", () => {
  if (!worker) return;
  worker.terminate(); worker=null; busy(false);
  status("Mineração cancelada. Nenhum bloco foi adicionado.");
});
$("verify").addEventListener("click", async () => {
  try { const ok=await render();status(ok ? "Verificação concluída: cadeia íntegra." : "Verificação concluída: alteração detectada!"); }
  catch(_) { status("Falha ao verificar a cadeia."); }
});
$("tamper").addEventListener("click", async () => {
  if(chain.length < 2){ status("Mine um bloco antes de testar a adulteração.");return; }
  chain[1].data += " [ALTERADO]";
  await render();
  status("O bloco #1 foi alterado. O hash registrado não corresponde mais aos dados.");
});
$("reset").addEventListener("click", () => { reset().catch(() => status("Falha ao preparar bloco gênese.")); });
reset().catch(() => status("SHA-256 indisponível: use HTTPS ou localhost."));
