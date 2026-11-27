"use strict";

/*
 * Orion Studio Semi-Pro / Test Bench.
 * All Ruby execution remains inside a disposable browser Web Worker.
 * The Worker receives only source and explicitly listed test inputs.
 * No code, drafts, progress, file bytes or results are posted to a server.
 */
(() => {
  const API = window.OrionStudio;
  if (!API) throw new Error("Orion Studio API unavailable");

  const $ = selector => document.querySelector(selector);
  const el = {
    select: $("#bench-select"),
    objective: $("#bench-objective"),
    hint: $("#bench-hint"),
    hintButton: $("#bench-hint-button"),
    tests: $("#bench-cases"),
    count: $("#bench-total"),
    run: $("#bench-run"),
    stop: $("#bench-stop"),
    output: $("#bench-output"),
    status: $("#bench-state"),
    score: $("#bench-score"),
    meter: $(".bench-meter"),
    meterFill: $("#bench-meter-fill"),
    customInput: $("#bench-custom-input"),
    customExpected: $("#bench-custom-expected"),
    customEnabled: $("#bench-custom-enabled"),
    progress: $("#bench-progress"),
    clearProgress: $("#bench-clear-progress"),
    draftStatus: $("#draft-status"),
    saveDraft: $("#save-draft"),
    loadDraft: $("#load-draft"),
    export: $("#export-source"),
    import: $("#import-source"),
    importInput: $("#import-input"),
    jump: $("#jump-bench"),
    testMarker: $("#bench-selftest")
  };

  const DRAFT_PREFIX = "ruby-orion-studio:v03:draft:";
  const PROGRESS_KEY = "ruby-orion-studio:v03:completed";
  const BOOT_TIMEOUT = 75_000;
  const CASE_TIMEOUT = 9_000;
  const CODE_LIMIT = 8_000;
  const INPUT_LIMIT = 4_000;
  const OUTPUT_LIMIT = 2_000;
  let busy = false;
  let worker = null;
  let bootTimer = null;
  let caseTimer = null;
  let selectedLabId = "";
  let requested = 0;
  let currentJob = null;
  let completed = restoreProgress();

  function normalize(value) {
    return String(value || "").replace(/\r\n/g, "\n").trimEnd();
  }

  function textNode(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    node.textContent = String(text);
    return node;
  }

  function setDraftStatus(message) {
    el.draftStatus.textContent = message;
  }

  function storageGet(key) {
    try { return localStorage.getItem(key); } catch { return null; }
  }

  function storageSet(key, value) {
    try { localStorage.setItem(key, value); return true; } catch { return false; }
  }

  function restoreProgress() {
    try {
      const value = JSON.parse(storageGet(PROGRESS_KEY) || "[]");
      return new Set(Array.isArray(value) ? value.filter(id => typeof id === "string" && /^\d{3}$/.test(id)) : []);
    } catch { return new Set(); }
  }

  function persistProgress() {
    storageSet(PROGRESS_KEY, JSON.stringify([...completed].sort()));
  }

  function updateProgress() {
    const labs = API.getLabs();
    const count = labs.filter(lab => completed.has(lab.id)).length;
    el.progress.textContent = count + " / " + labs.length;
    for (const node of document.querySelectorAll(".lab-card[data-lab-id]")) {
      node.dataset.completed = String(completed.has(node.dataset.labId));
    }
  }

  function draftKey() {
    const id = API.getActiveLab()?.id || "scratch";
    return DRAFT_PREFIX + (/^\d{3}$/.test(id) ? id : "scratch");
  }

  function saveDraft() {
    const source = API.getSource();
    if (!source.trim() || source.length > CODE_LIMIT) {
      setDraftStatus("Código vazio ou acima do limite de 8.000 caracteres.");
      return;
    }
    const data = JSON.stringify({ version: 1, source, saved_at: new Date().toISOString() });
    setDraftStatus(storageSet(draftKey(), data)
      ? "Rascunho salvo neste navegador. Nenhum envio ao servidor."
      : "Armazenamento indisponível. Exporte um arquivo .rb.");
  }

  function loadDraft() {
    const raw = storageGet(draftKey());
    if (!raw) { setDraftStatus("Nenhum rascunho salvo para este laboratório."); return; }
    try {
      const item = JSON.parse(raw);
      if (item.version !== 1 || typeof item.source !== "string" || item.source.length > CODE_LIMIT) {
        throw new Error("Formato de rascunho incompatível.");
      }
      setDraftStatus(API.setSource(item.source) ? "Rascunho restaurado." : "Finalize a execução antes de restaurar.");
    } catch {
      setDraftStatus("Rascunho inválido ou indisponível.");
    }
  }

  function exportSource() {
    const code = API.getSource();
    if (!code.trim()) { setDraftStatus("Nada para exportar."); return; }
    const filename = "orion-" + (API.getActiveLab()?.id || "playground") + ".rb";
    const blob = new Blob([code], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.hidden = true;
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 3000);
    setDraftStatus("Arquivo " + filename + " exportado localmente.");
  }

  async function importSource() {
    const file = el.importInput.files?.[0];
    el.importInput.value = "";
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".rb") || file.size > 16_384) {
      setDraftStatus("Aceitamos apenas arquivos .rb de até 16 KiB.");
      return;
    }
    try {
      const code = await file.text();
      if (code.length > CODE_LIMIT) throw new Error("Código acima de 8.000 caracteres.");
      setDraftStatus(API.setSource(code)
        ? "Código importado localmente. Execute os testes quando desejar."
        : "Finalize a execução antes de importar.");
    } catch (error) {
      setDraftStatus("Importação recusada: " + String(error.message || error).slice(0,140));
    }
  }

  function chooseLab(id) {
    if (!id) {
      selectedLabId = "";
      el.select.value = "";
      refreshLab();
      return;
    }
    if (busy || API.isBusy()) return;
    if (!API.loadLabById(id, true)) return;
    selectedLabId = id;
    el.select.value = id;
    refreshLab();
  }

  function selectedLab() {
    return API.getLabs().find(lab => lab.id === selectedLabId) || null;
  }

  function testCases(lab) {
    if (!lab) return [];
    if (Array.isArray(lab.tests) && lab.tests.length) return lab.tests.slice(0, 5);
    return [{ name: "Saída do laboratório", input: "", expected: lab.expected }];
  }

  function refreshLab() {
    const lab = selectedLab();
    if (!lab) {
      el.objective.textContent = "Sem laboratório selecionado. Use seu código do Playground e adicione um teste personalizado para executar.";
      el.hint.textContent = "";
      el.hint.hidden = true;
      el.hintButton.disabled = true;
      el.tests.replaceChildren(textNode("p", "bench-empty", "Selecione um laboratório ou habilite o teste personalizado."));
      el.count.textContent = "0 CASOS";
    } else {
      el.objective.textContent = lab.objective || lab.summary;
      el.hint.textContent = lab.hint || "Experimente dividir o problema em pequenos passos.";
      el.hint.hidden = true;
      el.hintButton.disabled = false;
      el.hintButton.setAttribute("aria-expanded", "false");
      const cases = testCases(lab);
      el.count.textContent = cases.length + " CASOS";
      el.tests.replaceChildren(...cases.map((test, index) => {
        const card = textNode("div", "bench-testcase", "");
        card.append(textNode("small", "", "TEST " + String(index + 1).padStart(2, "0")));
        card.append(textNode("strong", "", " / " + test.name));
        const incoming = textNode("pre", "", "STDIN:\n" + (test.input || "(vazio)"));
        const expected = textNode("pre", "", "ESPERADO:\n" + (test.expected || "(vazio)"));
        card.append(incoming, expected);
        return card;
      }));
    }
    updateProgress();
  }

  function labsReady() {
    const labs = API.getLabs();
    el.select.replaceChildren(textNode("option", "", "Código livre / teste personalizado"));
    el.select.options[0].value = "";
    for (const lab of labs) {
      const option = textNode("option", "", "EXP-" + lab.id + " · " + lab.title);
      option.value = lab.id;
      el.select.append(option);
    }
    selectedLabId = API.getActiveLab()?.id || "";
    el.select.value = selectedLabId;
    refreshLab();
    if (new URLSearchParams(location.search).get("benchtest") === "1") {
      chooseLab("001"); // Known deterministic suite for browser smoke checks.
      el.testMarker.dataset.result = "pending";
      startSuite();
    }
  }

  function buildCases() {
    const lab = selectedLab();
    const cases = testCases(lab).map(test => ({
      name: test.name,
      input: String(test.input),
      expected: String(test.expected)
    }));
    if (el.customEnabled.checked) {
      if (el.customInput.value.length > INPUT_LIMIT || el.customExpected.value.length > OUTPUT_LIMIT)
        throw new Error("Teste personalizado acima do limite permitido.");
      cases.push({
        name: "Teste personalizado",
        input: el.customInput.value,
        expected: el.customExpected.value
      });
    }
    if (cases.length < 1 || cases.length > 6) throw new Error("Escolha de 1 a 6 casos de teste.");
    if (cases.some(test => test.input.length > INPUT_LIMIT || test.expected.length > OUTPUT_LIMIT))
      throw new Error("Uma entrada ou saída esperada ultrapassa o limite.");
    return cases;
  }

  function setBusy(value) {
    busy = value;
    document.body.dataset.benchRunning = String(value);
    el.run.disabled = value;
    el.stop.disabled = !value;
    el.select.disabled = value;
    $("#run-code").disabled = value;
  }

  function resetTimers() {
    clearTimeout(bootTimer);
    clearTimeout(caseTimer);
    bootTimer = null;
    caseTimer = null;
  }

  function stopWorker() {
    resetTimers();
    if (worker) worker.terminate();
    worker = null;
    setBusy(false);
  }

  function setMeter(percent) {
    const value = Math.max(0, Math.min(100, percent));
    el.meterFill.style.width = value + "%";
    el.meter.setAttribute("aria-valuenow", String(value));
  }

  function failSuite(message) {
    stopWorker();
    el.status.textContent = "EXECUÇÃO INTERROMPIDA";
    el.score.textContent = "INCOMPLETO";
    el.output.prepend(textNode("p", "bench-empty", message));
    el.testMarker.dataset.result = "failed";
  }

  function timeoutCase() {
    failSuite("Tempo limite de 9 segundos por caso excedido. O Worker Ruby foi encerrado.");
  }

  function scheduleTimeout() {
    clearTimeout(caseTimer);
    caseTimer = setTimeout(timeoutCase, CASE_TIMEOUT);
  }

  function outputReport(test, response, index) {
    const ok = !response.error && !response.truncated &&
      normalize(response.output) === normalize(test.expected);
    const row = textNode("article", "bench-report " + (ok ? "ok" : "bad"), "");
    const header = textNode("div", "bench-report-header", "");
    header.append(textNode("strong", "", "TEST " + String(index + 1).padStart(2, "0") + " · " + test.name));
    header.append(textNode("span", "", (ok ? "✓ PASS" : "✕ FAIL") + " · " + response.durationMs + " ms"));
    row.append(header);
    if (!ok) {
      row.append(textNode("p", "", "Esperado"));
      row.append(textNode("pre", "", test.expected || "(vazio)"));
      row.append(textNode("p", "", response.error ? "Erro Ruby" : "Obtido"));
      row.append(textNode("pre", "", response.error || response.output || "(vazio)"));
      if (response.truncated) row.append(textNode("p", "", "Saída truncada; ajuste seu programa."));
    }
    el.output.append(row);
    return ok;
  }

  function onSuiteMessage(event) {
    const data = event.data || {};
    if (!currentJob || data.id !== currentJob.id || !busy) return;
    if (data.type === "booting") {
      el.status.textContent = "CARREGANDO RUBY / WASM";
      return;
    }
    if (data.type === "suite-ready") {
      clearTimeout(bootTimer);
      el.status.textContent = "EXECUTANDO TESTES";
      scheduleTimeout();
      return;
    }
    if (data.type === "fatal") {
      failSuite("Erro na VM Ruby: " + String(data.message || "Falha desconhecida").slice(0, 500));
      return;
    }
    if (data.type === "suite-case") {
      if (!Number.isInteger(data.index) || data.index !== currentJob.done ||
          data.index >= currentJob.cases.length) {
        failSuite("A VM enviou uma resposta fora da sequência esperada.");
        return;
      }
      const test = currentJob.cases[data.index];
      const passed = outputReport(test, data, data.index);
      currentJob.results.push(passed);
      currentJob.done++;
      el.score.textContent = currentJob.results.filter(Boolean).length +
        " / " + currentJob.cases.length + " PASS";
      setMeter(Math.round(currentJob.done * 100 / currentJob.cases.length));
      scheduleTimeout();
      return;
    }
    if (data.type === "suite-done") {
      if (currentJob.done !== currentJob.cases.length) {
        failSuite("A VM encerrou sem executar todos os casos.");
        return;
      }
      const allPassed = currentJob.results.every(Boolean);
      const lab = selectedLab();
      const builtInCount = testCases(lab).length;
      const builtInsPassed = lab && currentJob.results.slice(0, builtInCount).every(Boolean);
      stopWorker();
      el.status.textContent = allPassed ? "SUÍTE APROVADA" : "CORREÇÕES NECESSÁRIAS";
      if (builtInsPassed) {
        completed.add(lab.id);
        persistProgress();
        updateProgress();
      }
      el.testMarker.dataset.result = allPassed ? "passed" : "failed";
    }
  }

  function startSuite() {
    if (busy || API.isBusy()) return;
    let cases;
    try { cases = buildCases(); } catch (error) {
      el.status.textContent = "CONFIGURAÇÃO INVÁLIDA";
      el.output.replaceChildren(textNode("p", "bench-empty", error.message));
      return;
    }
    const code = API.getSource();
    if (!code.trim() || code.length > CODE_LIMIT) {
      el.output.replaceChildren(textNode("p", "bench-empty", "Escreva um programa Ruby no Playground (máximo 8.000 caracteres)."));
      return;
    }
    const id = ++requested;
    currentJob = { id, cases, done: 0, results: [] };
    el.output.replaceChildren();
    el.score.textContent = "0 / " + cases.length + " PASS";
    el.status.textContent = "INICIANDO MOTOR DE TESTES";
    setMeter(0);
    setBusy(true);
    try {
      worker = new Worker("/assets/ruby-worker.js", { type: "module", name: "orion-test-bench" });
      worker.onmessage = onSuiteMessage;
      worker.onerror = e => {
        e.preventDefault();
        failSuite("Falha ao carregar o Ruby/WebAssembly. Verifique conexão, integridade e CSP.");
      };
      worker.onmessageerror = () => failSuite("Falha de comunicação com o Web Worker.");
      bootTimer = setTimeout(() => failSuite("O runtime ultrapassou 75 segundos na inicialização."), BOOT_TIMEOUT);
      worker.postMessage({ type: "suite", id, code, cases: cases.map(x => ({ input: x.input })) });
    } catch (error) {
      failSuite("Não foi possível criar o motor de testes: " + String(error.message || error).slice(0, 150));
    }
  }

  el.select.addEventListener("change", e => chooseLab(e.target.value));
  el.hintButton.addEventListener("click", () => {
    el.hint.hidden = !el.hint.hidden;
    el.hintButton.setAttribute("aria-expanded", String(!el.hint.hidden));
    el.hintButton.textContent = el.hint.hidden ? "✦ Mostrar dica" : "✦ Ocultar dica";
  });
  el.run.addEventListener("click", startSuite);
  el.stop.addEventListener("click", () => {
    if (!busy) return;
    failSuite("O usuário interrompeu a suíte e descartou o Worker.");
  });
  el.saveDraft.addEventListener("click", saveDraft);
  el.loadDraft.addEventListener("click", loadDraft);
  el.export.addEventListener("click", exportSource);
  el.import.addEventListener("click", () => el.importInput.click());
  el.importInput.addEventListener("change", importSource);
  el.jump.addEventListener("click", () => { API.setPanel("bench"); location.hash = "#bench"; });
  el.clearProgress.addEventListener("click", () => {
    if (!window.confirm("Apagar o progresso de todos os laboratórios salvo neste navegador?")) return;
    completed.clear();
    persistProgress();
    updateProgress();
  });

  window.addEventListener("orion:lab-loaded", event => {
    selectedLabId = event.detail?.id || "";
    el.select.value = selectedLabId;
    refreshLab();
  });
  window.addEventListener("orion:labs-ready", labsReady);
  if (API.getLabs().length) labsReady();
})();
