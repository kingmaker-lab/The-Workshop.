"use strict";

const MAX_CODE = 8000;
const MAX_STDIN = 4000;
const MAX_FILE = 8 * 1024 * 1024;
const BOOT_TIMEOUT = 75_000;
const EXEC_TIMEOUT = 9_000;
const $ = selector => document.querySelector(selector);

const els = {
  editor: $("#source"), stdin: $("#stdin"),
  run: $("#run-code"), stop: $("#stop-code"), reset: $("#reset-code"),
  stdout: $("#stdout"), stderr: $("#stderr"),
  engine: $("#engine-status"), engineDot: $("#engine-dot"),
  elapsed: $("#elapsed"), counter: $("#code-count"),
  templateList: $("#template-list"), labGrid: $("#lab-grid"), labCount: $("#lab-count"),
  exercise: $("#exercise-check"), file: $("#file-input"),
  inspectFile: $("#inspect-file"), fileResults: $("#file-results"), fileError: $("#file-error"),
  selftest: $("#runtime-selftest")
};

const snippets = [
  { title: "Hello, Orion", code: 'puts "Alnitak ✦ Alnilam ✦ Mintaka"\nputs "Ruby #{RUBY_VERSION} está pronto!"\n' },
  { title: "Objetos Ruby", code: 'class Satellite\n  def initialize(name)\n    @name = name\n  end\n\n  def signal\n    "Sinal recebido de #{@name}"\n  end\nend\n\nputs Satellite.new("Orion").signal\n' },
  { title: "Iteração", code: 'stars = %w[Alnitak Alnilam Mintaka]\nstars.each_with_index do |name, i|\n  puts "#{i + 1} · #{name}"\nend\n' },
  { title: "JSON", code: 'require "json"\nframe = { protocol: "orion-ipc/1", payload: { ready: true } }\nputs JSON.pretty_generate(frame)\n' },
  { title: "STDIN", code: 'puts "Digite seu codinome:"\nname = gets&.strip || "explorador"\nputs "Bem-vindo, #{name}!"\n' }
];
const state = {
  worker: null, busy: false, sequence: 0, activeRun: 0,
  bootTimer: null, execTimer: null, startedAt: 0,
  activeLab: null, labs: [], testMode: false
};

function updateStatus(message, kind = "") {
  els.engine.textContent = message;
  els.engineDot.className = "dot-indicator " + kind;
}

function setBusy(value) {
  state.busy = value;
  els.run.disabled = value;
  els.stop.disabled = !value;
  els.reset.disabled = value;
}

function setOutput(out, err = "", elapsed = "READY") {
  els.stdout.textContent = out || "(Sem saída em stdout)";
  els.stderr.textContent = err || "Nenhum erro.";
  els.elapsed.textContent = elapsed;
}

function clearTimers() {
  clearTimeout(state.bootTimer);
  clearTimeout(state.execTimer);
  state.bootTimer = null;
  state.execTimer = null;
}

function markSelftest(status) {
  if (state.testMode) els.selftest.dataset.result = status;
}

function terminateWorker() {
  clearTimers();
  if (state.worker) state.worker.terminate();
  state.worker = null;
  state.activeRun = 0;
  setBusy(false);
}

function failRun(message) {
  terminateWorker();
  updateStatus("Runtime reiniciado", "error");
  setOutput("", message, "ERROR");
  els.exercise.className = "exercise-check failed";
  els.exercise.textContent = "A execução foi interrompida ou não pôde ser concluída.";
  markSelftest("failed");
}

function onRuntimeMessage(event) {
  const data = event.data || {};
  if (!state.busy) return;
  if (data.type === "booting") {
    updateStatus(data.message || "Carregando Ruby...", "busy");
    return;
  }
  if (data.id !== state.activeRun) return;
  if (data.type === "running") {
    clearTimeout(state.bootTimer);
    state.execTimer = setTimeout(() => failRun("Tempo de execução excedeu 9 segundos. O Worker foi encerrado."), EXEC_TIMEOUT);
    state.startedAt = performance.now();
    updateStatus("Executando Ruby...", "busy");
    els.elapsed.textContent = "RUNNING";
    return;
  }
  if (data.type === "fatal") {
    failRun(data.message || "Falha no interpretador Ruby.");
    return;
  }
  if (data.type !== "result") return;
  clearTimers();
  setBusy(false);
  updateStatus("Ruby pronto", "ready");
  const duration = Math.max(0, Math.round(performance.now() - state.startedAt));
  setOutput(data.output, data.error, duration + " ms");
  if (data.truncated) {
    els.stderr.textContent += "\nSaída limitada a 12.000 bytes por canal.";
  }
  if (state.activeLab && Array.isArray(state.activeLab.tests) && state.activeLab.tests.length) {
    els.exercise.className = "exercise-check";
    els.exercise.textContent = "Este desafio usa múltiplos testes. Abra o Test Bench para validar todos os casos.";
  } else if (state.activeLab) {
    const passed = !data.error && !data.truncated &&
      normalize(data.output) === normalize(state.activeLab.expected);
    els.exercise.className = "exercise-check " + (passed ? "passed" : "failed");
    els.exercise.textContent = passed
      ? "✓ EXP-" + state.activeLab.id + " concluído. Resultado esperado alcançado."
      : "Ainda não corresponde ao resultado esperado. Compare a saída e experimente novamente.";
  } else {
    els.exercise.className = "exercise-check";
    els.exercise.textContent = data.error ? "Confira o diagnóstico e tente novamente." : "Execução concluída. Experimente alterar o programa.";
  }
  if (state.testMode) markSelftest(!data.error && data.output.includes("ORION_RUBY_RUNTIME_OK") ? "passed" : "failed");
}

function normalize(text) {
  return String(text || "").replace(/\r\n/g, "\n").trimEnd();
}

function runCode() {
  if (state.busy || document.body.dataset.benchRunning === "true") return;
  const code = els.editor.value;
  const input = els.stdin.value;
  if (!code.trim()) { setOutput("", "Escreva um programa Ruby antes de executar.", "READY"); return; }
  if (code.length > MAX_CODE || input.length > MAX_STDIN) {
    setOutput("", "Limite: 8.000 caracteres de código e 4.000 de STDIN.", "READY");
    return;
  }
  setBusy(true);
  setOutput("Iniciando ambiente Ruby...", "", "BOOTING");
  updateStatus("Preparando runtime...", "busy");
  state.activeRun = ++state.sequence;
  state.startedAt = performance.now();
  try {
    if (!state.worker) {
      const worker = new Worker("/assets/ruby-worker.js", { type: "module", name: "ruby-orion-runtime" });
      worker.onmessage = onRuntimeMessage;
      worker.onerror = event => { event.preventDefault(); const diagnostic = [event.message, event.filename, event.lineno].filter(Boolean).join(" / ").slice(0, 450); failRun("Falha na inicialização do Web Worker Ruby: " + (diagnostic || "verifique conexão e CSP.")); };
      worker.onmessageerror = () => failRun("Erro na comunicação com o Worker.");
      state.worker = worker;
    }
    state.bootTimer = setTimeout(() => failRun("O runtime demorou demais para iniciar. Verifique a conexão ou tente novamente."), BOOT_TIMEOUT);
    state.worker.postMessage({ type: "run", id: state.activeRun, code, input });
  } catch (error) {
    failRun("Falha ao iniciar Worker: " + String(error && error.message || error));
  }
}

function setPanel(which) {
  const panel = ["playground", "labs", "inspector", "bench"].includes(which) ? which : "playground";
  for (const name of ["playground", "labs", "inspector", "bench"]) {
    const tab = $("#tab-" + name);
    const section = $("#panel-" + name);
    const selected = name === panel;
    tab.classList.toggle("active", selected);
    tab.setAttribute("aria-selected", String(selected));
    tab.tabIndex = selected ? 0 : -1;
    section.hidden = !selected;
  }
}

function renderTemplates() {
  els.templateList.replaceChildren(...snippets.map(snippet => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "template-button";
    button.textContent = snippet.title;
    button.addEventListener("click", () => {
      if (state.busy) return;
      state.activeLab = null;
      els.editor.value = snippet.code;
      els.stdin.value = "";
      updateCounter();
      els.exercise.className = "exercise-check";
      els.exercise.textContent = "Exemplo carregado. Execute e explore o resultado.";
      setPanel("playground");
      location.hash = "#playground";
      els.editor.focus();
    });
    return button;
  }));
}

function updateCounter() {
  els.counter.textContent = els.editor.value.length.toLocaleString("pt-BR") + " / 8.000";
  els.counter.style.color = els.editor.value.length > MAX_CODE ? "#ff8c98" : "";
}

function createTextNode(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  node.textContent = String(text);
  return node;
}

function loadLab(lab, stay = false) {
  if (state.busy || document.body.dataset.benchRunning === "true") return;
  state.activeLab = lab;
  els.editor.value = lab.code;
  els.stdin.value = Array.isArray(lab.tests) && lab.tests[0] ? lab.tests[0].input : "";
  updateCounter();
  if (!stay) { setPanel("playground"); location.hash = "#playground"; }
  els.exercise.className = "exercise-check";
  els.exercise.textContent = "EXP-" + lab.id + " · Resultado esperado: " + JSON.stringify(lab.expected.trimEnd()) + ". " + lab.limitation;
  if (!stay) els.editor.focus();
  window.dispatchEvent(new CustomEvent("orion:lab-loaded", { detail: { id: lab.id } }));
}

function renderLabs() {
  els.labCount.textContent = String(state.labs.length).padStart(2, "0") + " LABORATÓRIOS INTERATIVOS";
  const cards = state.labs.map(lab => {
    const card = createTextNode("article", "lab-card", "");
    card.dataset.labId = lab.id;
    card.append(createTextNode("span", "lab-id", "EXP-" + lab.id + " / " + lab.pillar));
    card.append(createTextNode("h4", "", lab.title));
    card.append(createTextNode("p", "", lab.summary));
    const footer = createTextNode("footer", "", "");
    footer.append(createTextNode("span", "", lab.level));
    const button = createTextNode("button", "", "Abrir no Studio ↗");
    button.type = "button";
    button.addEventListener("click", () => loadLab(lab));
    footer.append(button);
    card.append(footer);
    return card;
  });
  els.labGrid.replaceChildren(...cards);
}

async function loadLabs() {
  try {
    const response = await fetch("/data/labs.json", { cache: "no-cache" });
    if (!response.ok) throw new Error("HTTP " + response.status);
    const data = await response.json();
    if (data.schema_version !== 1 || !Array.isArray(data.labs)) throw new Error("Catálogo incompatível");
    state.labs = data.labs.filter(x => x && /^[0-9]{3}$/.test(x.id) &&
      typeof x.code === "string" && typeof x.expected === "string" &&
      typeof x.title === "string" && typeof x.summary === "string" &&
      typeof x.level === "string" && typeof x.pillar === "string" &&
      typeof x.limitation === "string");
    renderLabs();
    window.dispatchEvent(new Event("orion:labs-ready"));
  } catch (error) {
    els.labGrid.replaceChildren(createTextNode("p", "", "Não foi possível carregar os laboratórios: " + error.message));
    els.labCount.textContent = "INDISPONÍVEIS";
  }
}

function detectFormat(bytes) {
  const starts = arr => arr.every((value, index) => bytes[index] === value);
  if (starts([0x7f, 0x45, 0x4c, 0x46])) return "ELF";
  if (starts([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])) return "PNG";
  if (starts([0x25, 0x50, 0x44, 0x46, 0x2d])) return "PDF";
  if (starts([0x50, 0x4b, 0x03, 0x04])) return "ZIP";
  if (starts([0x47, 0x49, 0x46, 0x38])) return "GIF";
  if (starts([0x4d, 0x5a])) {
    if (bytes.length >= 0x40) {
      const offset = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength).getUint32(0x3c, true);
      if (offset + 4 <= bytes.length && bytes[offset] === 0x50 && bytes[offset + 1] === 0x45 &&
        bytes[offset + 2] === 0 && bytes[offset + 3] === 0) return "PE";
    }
    return "MZ / possível PE";
  }
  return "Não identificada";
}

function entropy(bytes) {
  const n = Math.min(4096, bytes.length);
  if (!n) return 0;
  const counts = new Uint32Array(256);
  for (let i = 0; i < n; i++) counts[bytes[i]]++;
  let result = 0;
  for (const count of counts) {
    if (!count) continue;
    const p = count / n;
    result -= p * Math.log2(p);
  }
  return Number(result.toFixed(4));
}

function toHex(buffer) {
  return Array.from(new Uint8Array(buffer), value => value.toString(16).padStart(2, "0")).join("");
}

function showFileResults(rows) {
  const list = [];
  for (const [name, value] of rows) {
    const wrap = document.createElement("div");
    wrap.append(createTextNode("dt", "", name), createTextNode("dd", "", value));
    list.push(wrap);
  }
  els.fileResults.replaceChildren(...list);
}

async function inspectFile() {
  els.fileError.textContent = "";
  const file = els.file.files && els.file.files[0];
  if (!file) return;
  if (file.size > MAX_FILE) {
    els.fileError.textContent = "O limite é de 8 MiB. Arquivos maiores devem ser analisados com a CLI local.";
    return;
  }
  els.inspectFile.disabled = true;
  try {
    const bytes = new Uint8Array(await file.arrayBuffer());
    const [sha256, sha512] = await Promise.all([
      crypto.subtle.digest("SHA-256", bytes), crypto.subtle.digest("SHA-512", bytes)
    ]);
    showFileResults([
      ["ARQUIVO", file.name],
      ["TAMANHO", file.size.toLocaleString("pt-BR") + " bytes"],
      ["ASSINATURA", detectFormat(bytes)],
      ["ENTROPIA / 4KiB", entropy(bytes).toFixed(4) + " bits/byte"],
      ["SHA-256", toHex(sha256)],
      ["SHA-512", toHex(sha512)]
    ]);
    // No fetch is performed: buffers stay in the browser.
  } catch (error) {
    els.fileError.textContent = "Não foi possível analisar o arquivo: " + String(error && error.message || error);
  } finally {
    els.inspectFile.disabled = false;
  }
}

function hashRoute() {
  const current = location.hash.slice(1);
  setPanel(current);
}

document.querySelectorAll("[data-panel]").forEach(tab => tab.addEventListener("click", () => {
  location.hash = "#" + tab.dataset.panel;
  setPanel(tab.dataset.panel);
}));
window.addEventListener("hashchange", hashRoute);
els.run.addEventListener("click", runCode);
els.stop.addEventListener("click", () => {
  if (!state.busy) return;
  terminateWorker();
  updateStatus("Execução interrompida", "error");
  setOutput("", "A execução foi interrompida e o Worker reiniciado.", "STOPPED");
  markSelftest("failed");
});
els.reset.addEventListener("click", () => {
  if (state.busy) return;
  els.editor.value = snippets[0].code;
  els.stdin.value = "";
  state.activeLab = null;
  updateCounter();
  setOutput("# Ambiente restaurado. Pronto para começar.");
  els.exercise.className = "exercise-check";
  els.exercise.textContent = "Carregue um laboratório para verificar seu resultado.";
});
els.editor.addEventListener("input", updateCounter);
els.editor.addEventListener("keydown", event => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    event.preventDefault();
    runCode();
  }
  if (event.key === "Tab" && !event.ctrlKey && !event.metaKey) {
    event.preventDefault();
    els.editor.setRangeText("  ", els.editor.selectionStart, els.editor.selectionEnd, "end");
    updateCounter();
  }
});
els.file.addEventListener("change", () => {
  els.inspectFile.disabled = !els.file.files.length;
  els.fileError.textContent = "";
});
els.inspectFile.addEventListener("click", inspectFile);

function boot() {
  state.testMode = new URLSearchParams(location.search).get("selftest") === "1";
  els.editor.value = state.testMode ? 'puts "ORION_RUBY_RUNTIME_OK"\n' : snippets[0].code;
  updateCounter();
  renderTemplates();
  loadLabs();
  hashRoute();
  if (state.testMode) {
    markSelftest("pending");
    setTimeout(runCode, 100);
  }
}
window.OrionStudio = Object.freeze({
  getLabs: () => state.labs.slice(),
  getActiveLab: () => state.activeLab,
  isBusy: () => state.busy,
  getSource: () => els.editor.value,
  setSource: code => {
    if (state.busy || document.body.dataset.benchRunning === "true" ||
        typeof code !== "string" || code.length > MAX_CODE) return false;
    els.editor.value = code;
    updateCounter();
    return true;
  },
  loadLabById: (id, stay = false) => {
    const lab = state.labs.find(item => item.id === id);
    if (!lab) return false;
    loadLab(lab, stay);
    return true;
  },
  setPanel
});
boot();
