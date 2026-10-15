import { VulpesGame } from './vulpes-engine.js';
import { DATA } from './vulpes-data.js';

const STORAGE_KEY = 'wolfpack-workshop-vulpes77-web-v01';
const $ = (selector) => document.querySelector(selector);
const log = $('#v77-output');
const form = $('#v77-form');
const input = $('#v77-input');
const hintPanel = $('#v77-objective');
let history = [];
let historyIndex = 0;
let busy = false;

function restore() {
  try {return JSON.parse(localStorage.getItem(STORAGE_KEY));}
  catch {return null;}
}
const game = new VulpesGame(restore());
function persist() {
  try {localStorage.setItem(STORAGE_KEY, JSON.stringify(game.snapshot()));}
  catch { /* Navegação privada ou quota excedida: ainda jogável na sessão atual. */ }
}
function line(text, kind = 'info') {
  const el = document.createElement('div');
  el.className = `vulpes-line ${({success:'ok', win:'ok', error:'bad', quit:'warn', system:'system', command:'command'})[kind] ?? ''}`;
  el.textContent = text; // Nunca interpretamos comandos/evidências como HTML.
  log.append(el);
  // Evita DOM ilimitado após muitas horas de uso.
  while (log.childElementCount > 220) log.firstElementChild.remove();
  log.scrollTop = log.scrollHeight;
}
function draw() {
  const idx = game.missionIndex;
  const mission = game.mission;
  $('#v77-stage').textContent = game.complete ? '03 / 03 ✓' : `${String(idx+1).padStart(2,'0')} / 03`;
  $('#v77-score').textContent = `${game.score} / 300 XP`;
  $('#v77-rank').textContent = game.rank;
  $('#v77-network').textContent = game.complete ? 'CONTIDA' : game.state.contained ? 'HOST ISOLADO' : 'MONITORANDO';
  $('#v77-progress').style.width = `${idx / DATA.missions.length * 100}%`;
  $('#v77-mission-title').textContent = mission ? mission.title : '✓ OPERAÇÃO NEXUS CONCLUÍDA';
  $('#v77-mission-brief').textContent = mission ? mission.lead.replaceAll('\\n','\n') : 'A ameaça foi descoberta, atribuída e contida. Operação concluída.';
  hintPanel.textContent = mission ? mission.target : `Campanha finalizada · patente ${game.rank}`;
  const nodeList = $('#v77-nodes');
  nodeList.replaceChildren();
  for (const [ip, node] of Object.entries(DATA.network)) {
    const div = document.createElement('div');
    div.className = `vulpes-node ${mission?.unlock.includes(ip) ? 'unlocked' : 'locked'}`;
    const emblem = document.createElement('span');
    emblem.textContent = mission?.unlock.includes(ip) ? '◉' : '◇';
    const body = document.createElement('div');
    const label = document.createElement('b');label.textContent = node.name;
    const desc = document.createElement('small');desc.textContent = `${ip} · ${mission?.unlock.includes(ip) ? 'ONLINE' : 'BLOQUEADO'}`;
    body.append(label, desc);div.append(emblem, body);nodeList.append(div);
  }
  const stages = $('#v77-stages');
  stages.replaceChildren();
  DATA.missions.forEach((stage, i) => {
    const item = document.createElement('li');
    item.className = i < idx ? 'done' : i === idx ? 'current' : 'locked';
    item.textContent = `${i < idx ? '✓ ' : ''}${stage.title.split(' / ')[1]}`;
    stages.append(item);
  });
  const promptText = game.prompt.trim();
  $('#v77-prompt-label').textContent = promptText;
  $('#v77-terminal-context').textContent = promptText.replace('vulpes77@','');
}
async function execute(command) {
  if (busy) return;
  busy = true;
  input.disabled = true;
  try {
    line(`${game.prompt}${command}`, 'command');
    const result = await game.perform(command);
    line(result.text, result.kind);
    persist();
    draw();
  } catch (error) {
    line(`Erro do motor local: ${error.message}`, 'error');
  } finally {
    busy = false;
    input.disabled = false;
    input.focus({preventScroll:true});
  }
}
form.addEventListener('submit', (event) => {
  event.preventDefault();
  const command = input.value.trim();
  if (!command) return;
  history.push(command);
  if (history.length > 100) history.shift();
  historyIndex = history.length;
  input.value = '';
  execute(command);
});
input.addEventListener('keydown', (event) => {
  if (event.key === 'ArrowUp') {
    if (!history.length) return;
    event.preventDefault();
    historyIndex = Math.max(0, historyIndex - 1);
    input.value = history[historyIndex];
  } else if (event.key === 'ArrowDown') {
    if (!history.length) return;
    event.preventDefault();
    historyIndex = Math.min(history.length, historyIndex + 1);
    input.value = historyIndex === history.length ? '' : history[historyIndex];
  }
});
$('#v77-clear').addEventListener('click', () => {
  log.replaceChildren();
  line('Tela limpa. Seu progresso continua salvo. Digite status para conferir.', 'system');
  input.focus({preventScroll:true});
});
$('#v77-restart').addEventListener('click', () => {
  if (!confirm('Recomeçar Incident Zero? A pontuação e o progresso salvos serão zerados.')) return;
  const result = game.reset();
  history = []; historyIndex = 0;
  log.replaceChildren();
  line(result.text, 'system');
  draw();persist();
  input.focus({preventScroll:true});
});
document.querySelectorAll('[data-v77-cmd]').forEach(button => {
  button.addEventListener('click', () => {
    input.value = button.dataset.v77Cmd;
    input.focus({preventScroll:true});
  });
});

log.replaceChildren();
line('V U L P E S - 7 7\nINCIDENT ZERO // TERMINAL OPS\nTHE WORKSHOP · CYBERSEC LAB\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
line(`v${DATA.version} | Rede 100% simulada | Nenhuma chamada de rede real`, 'system');
line(game.intro, 'info');
draw();
