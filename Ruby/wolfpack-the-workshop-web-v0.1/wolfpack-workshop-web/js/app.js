const STORAGE_KEY = 'wolfpack-workshop-ruby-v01';
const $ = selector => document.querySelector(selector);
const listEl = $('#mission-list');
const editor = $('#code-editor');
const output = $('#terminal-output');
const runButton = $('#run-btn');
const engineStatus = $('#engine-status');
const messageEl = $('#helper-message');
const nameDialog = $('#name-dialog');
let lessons = [];
let selected = 1;
let busy = false;
let currentWorker = null;
let runTimer = null;
let state = restore();

function restore() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
    if (saved && typeof saved === 'object') return {
      name: typeof saved.name === 'string' ? saved.name : '',
      completed: Array.isArray(saved.completed) ? saved.completed.filter(Number.isInteger) : [],
      codes: saved.codes && typeof saved.codes === 'object' ? saved.codes : {}
    };
  } catch { /* localStorage pode estar indisponível */ }
  return { name: '', completed: [], codes: {} };
}
function persist() {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); }
  catch { /* Sem persistência neste modo do navegador */ }
}
function unlocked(id) { return id === 1 || state.completed.includes(id - 1) || state.completed.includes(id); }
function isComplete(id) { return state.completed.includes(id); }
function completedCount() { return lessons.filter(l => isComplete(l.id)).length; }
function rank(n) { return n >= 12 ? 'KINGMAKER' : n >= 9 ? 'ALFA' : n >= 5 ? 'SENTINELA' : n >= 2 ? 'EXPLORADOR' : 'RECRUTA'; }
function lessonTitle(l) { return l.title.split(' | ')[0]; }

function updateHeader() {
  const count = completedCount();
  $('#player-name').textContent = state.name || 'RECRUTA';
  $('#player-name').title = 'Clique no lápis para alterar';
  $('#xp-value').innerHTML = `${count * 100} <span>XP</span>`;
  $('#completed-value').innerHTML = `${count} <span>/ 12</span>`;
  $('#rank-value').textContent = rank(count);
  $('#progress-bar').style.width = `${count / 12 * 100}%`;
}

function renderMissionList() {
  listEl.replaceChildren();
  const acts = ['ATO I', 'ATO II', 'ATO III', 'ATO FINAL'];
  for (const l of lessons) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = ['mission-item', l.id === selected ? 'active' : '', isComplete(l.id) ? 'done' : ''].join(' ');
    const available = unlocked(l.id);
    btn.disabled = !available || busy;
    btn.title = available ? l.title : 'Conclua a missão anterior para desbloquear';
    btn.setAttribute('aria-label', `Missão ${l.id}: ${lessonTitle(l)}${available ? '' : ' — bloqueada'}`);
    const number = document.createElement('span');
    number.className = 'mission-number';
    number.textContent = isComplete(l.id) ? '✓' : String(l.id).padStart(2, '0');
    const title = document.createElement('span');
    title.className = 'mission-text';
    title.textContent = lessonTitle(l);
    const status = document.createElement('span');
    status.className = 'mission-locked';
    status.textContent = available ? (isComplete(l.id) ? '✓' : '›') : '⌑';
    btn.append(number, title, status);
    btn.addEventListener('click', () => selectMission(l.id));
    listEl.append(btn);
  }
}

function updateLineNumbers() {
  const lineCount = Math.min(350, Math.max(1, editor.value.split('\n').length));
  $('#line-numbers').textContent = Array.from({ length: lineCount }, (_, n) => String(n + 1).padStart(2, '0')).join('\n');
}

function showMessage(text) {
  messageEl.textContent = text;
  messageEl.classList.toggle('visible', Boolean(text));
}
function setOutput(text, kind = '') {
  output.textContent = text;
  output.className = `terminal-output ${kind}`;
  output.scrollTop = output.scrollHeight;
}
function updateRunButton() {
  const hasNext = isComplete(selected) && lessons.some(l => l.id === selected + 1);
  runButton.textContent = busy ? '◌ EXECUTANDO...' : hasNext ? '→ PRÓXIMA MISSÃO' : isComplete(selected) ? '✓ REEXECUTAR' : '▶ EXECUTAR CÓDIGO';
  runButton.disabled = busy;
}
function selectMission(id) {
  if (busy || !unlocked(id)) return;
  const lesson = lessons.find(l => l.id === id);
  if (!lesson) return;
  selected = id;
  $('#mission-act').textContent = lesson.act;
  $('#mission-count').textContent = `MISSÃO ${String(id).padStart(2, '0')} / 12`;
  $('#mission-title').textContent = lessonTitle(lesson);
  $('#mission-scene').textContent = lesson.scene;
  $('#mission-theory').textContent = lesson.theory;
  $('#mission-example').textContent = lesson.example;
  $('#mission-task').textContent = lesson.task;
  $('#editor-tab-name').textContent = `missao_${String(id).padStart(2, '0')}.rb`;
  editor.value = state.codes[id] ?? `# Missão ${String(id).padStart(2, '0')} — ${lessonTitle(lesson)}\n`;
  updateLineNumbers();
  setOutput(`wolfpack@workshop:~$ ruby missao_${String(id).padStart(2, '0')}.rb\n\n> ${isComplete(id) ? 'Missão concluída. Pode revisar ou reexecutar.' : 'Aguardando seu código...'} `);
  showMessage('');
  renderMissionList();
  updateRunButton();
}
function checkRequirements(code, lesson) {
  if (!code.trim()) return 'O código está vazio.';
  for (const { pattern, message } of lesson.requirements) {
    if (!new RegExp(pattern).test(code)) return `Conceito ainda não aplicado: ${message}`;
  }
  return '';
}
function cancelWorker() {
  if (runTimer) clearTimeout(runTimer);
  runTimer = null;
  if (currentWorker) currentWorker.terminate();
  currentWorker = null;
}
function completeRun() {
  busy = false;
  cancelWorker();
  renderMissionList();
  updateRunButton();
}
function runChallenge({ retry = false } = {}) {
  if (busy) return;
  const lesson = lessons.find(l => l.id === selected);
  if (!retry && isComplete(selected) && lessons.some(l => l.id === selected + 1)) {
    selectMission(selected + 1);
    return;
  }
  const code = editor.value;
  const requirementsMessage = checkRequirements(code, lesson);
  if (requirementsMessage) { setOutput(`✗ ${requirementsMessage}`, 'error'); return; }
  if (code.length > 12000) { setOutput('✗ Código muito longo (máximo 12.000 caracteres).', 'error'); return; }
  if (!state.name) {
    openNameDialog();
    setOutput('Escolha seu codinome e clique novamente em EXECUTAR CÓDIGO.');
    return;
  }
  busy = true;
  renderMissionList();
  updateRunButton();
  setOutput('> Inicializando o motor Ruby por WebAssembly...\n> A primeira carga precisa de internet e pode demorar alguns segundos.');
  engineStatus.className = 'engine-status';
  engineStatus.innerHTML = '<i></i> MOTOR: CARREGANDO';
  try {
    currentWorker = new Worker('./js/ruby-worker.js', { type: 'module' });
    // O worker morre após o prazo: loops infinitos não travam o restante do site.
    const scheduleTimeout = (ms, reason) => {
      clearTimeout(runTimer);
      runTimer = setTimeout(() => {
        setOutput(`✗ ${reason}\n\nConfira loops e tente novamente.`, 'error');
        completeRun();
      }, ms);
    };
    scheduleTimeout(60000, 'O carregamento do interpretador excedeu 60 segundos. Verifique sua internet.');
    currentWorker.onmessage = ({ data }) => {
      if (data.type === 'status') {
        setOutput(`> ${data.message}\n> O código não é enviado ao nosso servidor.`);
      }
      if (data.type === 'case-start') {
        scheduleTimeout(7500, 'Execução excedeu 7,5 segundos para um caso de teste.');
        setOutput(`> Ruby carregado.\n> Validando seu código...\n> Teste ${data.index + 1} de ${lesson.cases.length}`);
      }
      if (data.type === 'fatal') {
        engineStatus.className = 'engine-status is-error';
        engineStatus.innerHTML = '<i></i> MOTOR: INDISPONÍVEL';
        setOutput(`✗ Não foi possível iniciar/executar Ruby.\n${data.message}\n\nConfirme sua conexão, o acesso ao CDN e tente novamente.`, 'error');
        completeRun();
      }
      if (data.type === 'result') {
        engineStatus.className = 'engine-status is-ready';
        engineStatus.innerHTML = '<i></i> RUBY WASM: ONLINE';
        if (data.success) {
          const firstTime = !state.completed.includes(selected);
          if (firstTime) state.completed.push(selected);
          state.completed.sort((a,b) => a - b);
          persist();
          updateHeader();
          const final = completedCount() === lessons.length;
          setOutput(`✓ ${data.count} teste(s) passaram. Código validado!\n${firstTime ? '+100 XP — missão concluída.' : 'Missão já concluída — XP mantido.'}\n\n${final ? '👑 KINGMAKER PROTOCOL // UNLOCKED\nA matilha foi restaurada. Você concluiu a campanha!' : '✓ Próxima missão desbloqueada.'}`, 'success');
        } else {
          const actual = data.actual?.trim() || '(nada)';
          const expected = data.expected?.trim();
          setOutput(`✗ TESTE ${data.index + 1} NÃO PASSOU\n${data.reason}\n${expected === undefined ? '' : `\nEsperado:\n${expected}\n`}\nSeu programa:\n${actual}`, 'error');
        }
        completeRun();
      }
    };
    currentWorker.onerror = (event) => {
      engineStatus.className = 'engine-status is-error';
      engineStatus.innerHTML = '<i></i> MOTOR: ERRO';
      setOutput('✗ Erro ao carregar o motor Ruby. Confira a conexão com a internet ou tente outro navegador.\n\n' + (event.message || ''), 'error');
      completeRun();
    };
    currentWorker.postMessage({ type: 'run', code, cases: lesson.cases });
  } catch (err) {
    setOutput(`✗ Navegador não permitiu iniciar o executor.\n${err.message}`, 'error');
    completeRun();
  }
}

function openNameDialog() {
  $('#codename-input').value = state.name || '';
  if (typeof nameDialog.showModal === 'function') nameDialog.showModal();
  else { const nick = prompt('Escolha seu codinome de lobo:'); if (nick?.trim()) { state.name = nick.trim().slice(0,24); persist(); updateHeader(); } }
}

function setupEvents() {
  editor.addEventListener('input', () => { state.codes[selected] = editor.value; persist(); updateLineNumbers(); });
  editor.addEventListener('keydown', e => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const { selectionStart: s, selectionEnd: t } = editor;
      editor.setRangeText('  ', s, t, 'end');
      editor.dispatchEvent(new Event('input'));
    }
    if (e.key === 'Enter' && e.ctrlKey) { e.preventDefault(); runChallenge({ retry: true }); }
  });
  runButton.addEventListener('click', () => runChallenge());
  $('#hint-btn').addEventListener('click', () => showMessage(`DICA: ${lessons[selected - 1].hint}`));
  $('#example-btn').addEventListener('click', () => { editor.value = lessons[selected - 1].example; editor.dispatchEvent(new Event('input')); showMessage('Exemplo carregado no editor. Agora adapte-o à missão.'); editor.focus(); });
  $('#solution-btn').addEventListener('click', () => {
    if (confirm('Ver a solução completa? Você pode aprender mais tentando primeiro.')) showMessage(`SOLUÇÃO PARA ESTUDAR:\n${lessons[selected - 1].solution}`);
  });
  $('#clear-output').addEventListener('click', () => setOutput('wolfpack@workshop:~$\n> Terminal limpo.'));
  $('#reset-progress').addEventListener('click', () => {
    if (!confirm('Reiniciar todas as 12 missões e apagar seu XP e seus códigos salvos neste navegador?')) return;
    cancelWorker(); busy = false;
    state = { name: state.name, completed: [], codes: {} };
    persist(); updateHeader(); selectMission(1);
  });
  $('#edit-name').addEventListener('click', openNameDialog);
  $('#cancel-name').addEventListener('click', () => nameDialog.close());
  $('#name-form').addEventListener('submit', event => {
    const value = $('#codename-input').value.trim();
    if (value.length < 2) { event.preventDefault(); $('#codename-input').setCustomValidity('Use pelo menos dois caracteres.'); $('#codename-input').reportValidity(); return; }
    state.name = value.slice(0,24); persist(); updateHeader();
  });
  $('#codename-input').addEventListener('input', event => event.target.setCustomValidity(''));
  const navItems = document.querySelectorAll('.nav-link');
  const sectionNames = { inicio:'OVERVIEW', aplicacoes:'APPLICATIONS', jogar:'RUBY PROTOCOL', metodo:'METHOD' };
  const activateNav = () => {
    const id = location.hash.slice(1) || 'inicio';
    navItems.forEach(item => item.classList.toggle('active', item.dataset.nav === id));
    $('#breadcrumb-current').textContent = sectionNames[id] || 'OVERVIEW';
  };
  window.addEventListener('hashchange', activateNav);
  activateNav();
}

async function start() {
  try {
    const res = await fetch('./data/lessons.json');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    lessons = await res.json();
    if (!Array.isArray(lessons) || lessons.length !== 12) throw new Error('Campanha incompleta.');
    state.completed = state.completed.filter(n => lessons.some(l => l.id === n));
    setupEvents();
    updateHeader();
    selectMission(lessons.find(l => unlocked(l.id) && !isComplete(l.id))?.id || 12);
  } catch (error) {
    $('#mission-title').textContent = 'Não foi possível carregar as missões';
    setOutput(`✗ ${error.message}\n\nExecute o site por um servidor HTTP local (veja README.md).`, 'error');
  }
}
start();
