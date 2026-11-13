"use strict";
// HEART_005: deterministic *untrained* scaled dot-product causal attention.
// Browser teaching model only; independent from Python and HEART_004 weights.
(() => {
  const input = document.getElementById("attention-input");
  const matrix = document.getElementById("attention-matrix");
  const focus = document.getElementById("attention-focus");
  const status = document.getElementById("attention-stats");
  const explanation = document.getElementById("attention-detail");
  if (!input || !matrix || !focus || !status || !explanation ||
      typeof encode !== "function") return;

  const dimension = 8;
  const maxTokens = 14;
  let seed = 5052026;
  const random = () => {
    seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
    return seed / 4294967296;
  };
  const projection = () => Array.from({length: dimension}, () =>
    Array.from({length: dimension}, () => (random() - 0.5) * 0.5));
  const Wq = projection(), Wk = projection(), Wv = projection();
  const project = (vector, w) => Array.from({length: dimension}, (_, column) =>
    vector.reduce((sum, value, index) => sum + value * w[index][column], 0));
  const vectorFor = (id, position) => Array.from({length: dimension}, (_, axis) => {
    // Stable toy token vector; no model file, no online training or API.
    const noise = Math.sin(id * 12.9898 + axis * 78.233) * 43758.5453;
    const tokenComponent = (noise - Math.floor(noise) - .5) * .5;
    const angle = position / Math.pow(10000, 2 * Math.floor(axis / 2) / dimension);
    return tokenComponent + (axis % 2 === 0 ? Math.sin(angle) : Math.cos(angle));
  });
  function compute(ids) {
    const x = ids.map((id, i) => vectorFor(id, i));
    const q = x.map(v => project(v, Wq));
    const k = x.map(v => project(v, Wk));
    const values = x.map(v => project(v, Wv));
    const weights = [];
    const output = [];
    for (let i = 0; i < ids.length; i++) {
      const logits = [];
      for (let j = 0; j <= i; j++)
        logits.push(q[i].reduce((s, value, d) => s + value * k[j][d], 0) / Math.sqrt(dimension));
      const ceiling = Math.max(...logits);
      const scaled = logits.map(value => Math.exp(value - ceiling));
      const denominator = scaled.reduce((a, b) => a + b, 0);
      const row = Array(ids.length).fill(0);
      for (let j = 0; j <= i; j++) row[j] = scaled[j] / denominator;
      weights.push(row);
      output.push(Array.from({length: dimension}, (_, d) =>
        row.reduce((sum, a, j) => sum + a * values[j][d], 0)));
    }
    return {weights, output};
  }
  function makeCell(tag, content) {
    const element = document.createElement(tag);
    element.textContent = content;
    return element;
  }
  function draw() {
    const raw = input.value.slice(0, 160);
    const all = encode(raw);
    const ids = all.slice(0, maxTokens);
    matrix.textContent = "";
    if (ids.length === 0) {
      focus.max = "0"; focus.value = "0";
      status.textContent = "Digite algum texto para gerar a matriz causal.";
      explanation.textContent = "Nenhum token disponível.";
      return;
    }
    const result = compute(ids);
    focus.max = String(ids.length - 1);
    if (+focus.value >= ids.length) focus.value = String(ids.length - 1);
    const selected = Number(focus.value);
    const table = document.createElement("table");
    table.className = "attention-heatmap";
    table.setAttribute("aria-label", "Matriz de pesos da atenção causal: linhas consultas, colunas chaves");
    const head = document.createElement("tr");
    head.append(makeCell("th", "Q / K"));
    for (let j = 0; j < ids.length; j++) {
      const label = makeCell("th", String(ids[j]));
      label.setAttribute("scope", "col");
      head.append(label);
    }
    table.append(head);
    for (let i = 0; i < ids.length; i++) {
      const row = document.createElement("tr");
      if (i === selected) row.className = "attention-active";
      const rowHeader = makeCell("th", String(ids[i]));
      rowHeader.setAttribute("scope", "row");
      row.append(rowHeader);
      for (let j = 0; j < ids.length; j++) {
        const future = j > i;
        const weight = result.weights[i][j];
        const cell = makeCell("td", future ? "·" : weight.toFixed(2));
        cell.className = future ? "attention-masked" :
          "attention-level-" + Math.min(5, Math.floor(weight * 6));
        cell.setAttribute("aria-label", future ?
          "Token " + i + " não pode observar token futuro " + j :
          "Token " + i + " observa token " + j + " com peso " + weight.toFixed(4));
        row.append(cell);
      }
      table.append(row);
    }
    matrix.append(table);
    status.textContent = "TOKENS USADOS: " + ids.length + "/" + all.length +
      " | DIMENSÕES: " + dimension + " | MÁSCARA: causal / futuro bloqueado" +
      (all.length > ids.length ? " | Sequência truncada para manter o laboratório leve." : "");
    const allowed = result.weights[selected].slice(0, selected + 1);
    const total = allowed.reduce((a, b) => a + b, 0);
    explanation.textContent =
      "Consulta " + selected + " (token " + ids[selected] +
      "): só pode consultar posições 0 a " + selected +
      ". Soma dos pesos permitidos = " + total.toFixed(4) +
      ". Vetor de saída: [" + result.output[selected].map(n => n.toFixed(3)).join(", ") + "].";
  }
  input.addEventListener("input", () => {focus.value = "0"; draw();});
  focus.addEventListener("input", draw);
  draw();
})();
