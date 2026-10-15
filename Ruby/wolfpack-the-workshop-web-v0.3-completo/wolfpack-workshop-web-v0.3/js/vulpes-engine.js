/**
 * VULPES-77 WEB: port controlado do motor do jogo Ruby 0.1.0.
 * Fonte de verdade: ../source/vulpes77/lib/vulpes77.rb e export_vulpes.rb.
 * Tudo aqui é uma simulação em memória: scan/connect/contain jamais fazem I/O de rede.
 */
import { DATA } from './vulpes-data.js';

export const VULPES_VERSION = DATA.version;
const MISSIONS = DATA.missions;
const NETWORK = DATA.network;
const FILES = DATA.files;
const MAX_JOURNAL = 40;

const empty = () => ({
  version: VULPES_VERSION, mission_index: 0, score: 0, penalty: 0,
  hint_used: false, contained: false, scanned: [], session: null, journal: []
});
const clamp = (n, a, b) => Math.max(a, Math.min(b, Number.isFinite(Number(n)) ? Math.trunc(Number(n)) : a));
const reply = (text, kind = 'info') => ({text, kind});

/** Subconjunto de Shellwords.split: aspas simples/duplas e escapes, sem shell real. */
export function splitShellWords(line) {
  const result = [];
  let word = '', active = false, quote = null;
  for (let i = 0; i < line.length; i++) {
    const c = line[i];
    if (quote === "'") {
      if (c === "'") quote = null;
      else word += c;
    } else if (quote === '"') {
      if (c === '"') quote = null;
      else if (c === '\\' && i + 1 < line.length && ['\\', '"', '$', '`', '\n'].includes(line[i + 1])) {
        const next = line[++i]; if (next !== '\n') word += next;
      } else word += c;
    } else if (/\s/.test(c)) {
      if (active) {result.push(word); word = ''; active = false;}
    } else if (c === '"' || c === "'") {
      quote = c; active = true;
    } else if (c === '\\') {
      if (i + 1 >= line.length) throw new Error('escape no final da entrada');
      word += line[++i]; active = true;
    } else {word += c; active = true;}
  }
  if (quote) throw new Error('aspas não fechadas');
  if (active) result.push(word);
  return result;
}

export class VulpesGame {
  constructor(saved = null) {this.state = empty(); if (saved) this.restore(saved);}
  get missionIndex() {return this.state.mission_index;}
  get score() {return this.state.score;}
  get complete() {return this.missionIndex >= MISSIONS.length;}
  get mission() {return MISSIONS[this.missionIndex] ?? null;}
  get rank() {
    return this.score >= 270 ? 'VULPES OPERATOR' : this.score >= 210 ? 'SENIOR ANALYST' : this.score >= 150 ? 'THREAT HUNTER' : 'SOC RECRUIT';
  }
  get prompt() {
    const s = this.state.session;
    const context = s ? `${NETWORK[s.host].name}:${s.port}` : 'nexus';
    return `vulpes77@${context}$ `;
  }
  get intro() {
    if (this.complete) return `Operação NEXUS concluída. Pontuação: ${this.score}/300. Digite 'status', 'novo' ou 'sair'.`;
    const m = this.mission;
    return `${m.title}\n${m.lead.replaceAll('\\n', '\n')}\n\nOBJETIVO: ${m.target}\nDigite 'help' para conhecer os comandos.`;
  }
  reset() {this.state = empty(); return reply(`Nova operação iniciada.\n\n${this.intro}`, 'success');}
  snapshot() {return JSON.parse(JSON.stringify(this.state));}
  /** Importação defensiva do save do navegador; preserva bloqueios do jogo Ruby. */
  restore(raw) {
    try {
      if (!raw || typeof raw !== 'object' || raw.version !== VULPES_VERSION) return false;
      if (!Number.isInteger(raw.mission_index) || raw.mission_index < 0 || raw.mission_index > MISSIONS.length) return false;
      const idx = raw.mission_index;
      const unlocked = idx < MISSIONS.length ? MISSIONS[idx].unlock : [];
      const scanned = Array.isArray(raw.scanned) ? [...new Set(raw.scanned.filter(ip => typeof ip === 'string' && unlocked.includes(ip)))] : [];
      let session = null;
      if (raw.session && typeof raw.session === 'object' && scanned.includes(raw.session.host)) {
        const port = Number(raw.session.port);
        if (Number.isInteger(port) && Object.hasOwn(NETWORK[raw.session.host].ports, String(port))) session = {host:raw.session.host, port};
      }
      this.state = {
        version: VULPES_VERSION, mission_index: idx,
        score: clamp(raw.score, 0, 300), penalty: clamp(raw.penalty, 0, 100),
        hint_used: raw.hint_used === true,
        contained: idx === 2 && raw.contained === true,
        scanned, session,
        journal: Array.isArray(raw.journal) ? raw.journal.filter(e => typeof e === 'string').slice(-MAX_JOURNAL).map(s => s.slice(0, 240)) : []
      };
      return true;
    } catch {return false;}
  }
  addJournal(note) {this.state.journal.push(`M${this.missionIndex+1}: ${note}`); this.state.journal = this.state.journal.slice(-MAX_JOURNAL);}
  serviceFiles() {const s = this.state.session; return s ? FILES[`${s.host}:${s.port}`] : null;}
  status() {
    if (this.complete) return reply(`CAMPANHA CONCLUÍDA\nPontuação: ${this.score}/300 | Rank: ${this.rank}\nUse novo para jogar novamente.`, 'success');
    return reply(`${this.mission.title}\nOBJETIVO: ${this.mission.target}\nPontos acumulados: ${this.score}\nPontos possíveis nesta missão: ${Math.max(100 - this.state.penalty, 0)}\nHost em sessão: ${this.state.session?.host ?? 'nenhum'}\nIsolamento WEB-01: ${this.state.contained ? 'sim' : 'não'}`);
  }
  map() {
    const rows = Object.entries(NETWORK).map(([ip, node]) => {
      const lock = this.mission.unlock.includes(ip) ? 'ONLINE' : 'BLOQUEADO';
      return `${ip.padEnd(13)} ${node.name.padEnd(10)} [${lock}]`;
    });
    return reply(`NEXUS / SEGMENTO DE TREINAMENTO\n${rows.join('\n')}\nNenhum endereço corresponde a um alvo real.`);
  }
  scan(args) {
    if (args.length !== 1) return reply('Uso: scan <IP> (veja map)', 'error');
    const ip = args[0], node = NETWORK[ip];
    if (!node) return reply('Host não existe na topologia virtual.', 'error');
    if (!this.mission.unlock.includes(ip)) return reply('Acesso ao segmento ainda bloqueado nesta missão.', 'error');
    if (!this.state.scanned.includes(ip)) this.state.scanned.push(ip);
    this.addJournal(`SCAN ${node.name} ${ip}`);
    return reply(`${node.name} (${ip})\n${DATA.port_order[ip].map(port => `${port}/tcp open ${node.ports[port]}`).join('\n')}`, 'success');
  }
  connect(args) {
    if (args.length !== 1) return reply('Uso: connect <IP>:<porta>', 'error');
    const match = /^(\d+\.\d+\.\d+\.\d+):(\d{1,5})$/.exec(args[0]);
    if (!match) return reply('Destino inválido. Ex.: connect 10.77.0.12:8080', 'error');
    const ip = match[1], port = Number(match[2]);
    if (!this.mission.unlock.includes(ip)) return reply('Host bloqueado ou desconhecido.', 'error');
    if (!this.state.scanned.includes(ip)) return reply('Primeiro faça scan no host.', 'error');
    const node = NETWORK[ip];
    if (!node || !Object.hasOwn(node.ports, String(port))) return reply('Porta não disponível nesse host virtual.', 'error');
    this.state.session = {host:ip, port};
    this.addJournal(`CONNECT ${node.name}:${port}`);
    return reply(`Conectado a ${node.name} / ${node.ports[port]}. Use ls ou cat.`, 'success');
  }
  disconnect() {this.state.session = null; return reply('Sessão encerrada.');}
  ls() {
    const files = this.serviceFiles();
    if (!files) return reply('Não há sessão ativa. Use connect.', 'error');
    return reply(`ARQUIVOS DISPONÍVEIS\n${Object.keys(files).sort().join('\n')}`);
  }
  cat(args) {
    if (args.length !== 1) return reply('Uso: cat <arquivo>', 'error');
    if (!this.state.session) return reply('Conecte-se a um serviço antes.', 'error');
    const content = this.serviceFiles()?.[args[0]];
    if (content === undefined) return reply('Arquivo não encontrado no serviço atual.', 'error');
    const s = this.state.session;
    this.addJournal(`READ ${s.host}:${s.port}/${args[0]}`);
    return reply(content);
  }
  grep(args) {
    if (args.length !== 2) return reply('Uso: grep <texto> <arquivo>', 'error');
    if (!this.state.session) return reply('Conecte-se a um serviço antes.', 'error');
    const content = this.serviceFiles()?.[args[1]];
    if (content === undefined) return reply('Arquivo não encontrado.', 'error');
    const lines = content.split(/(?<=\n)/).filter(line => line.toLowerCase().includes(args[0].toLowerCase()));
    this.addJournal(`GREP '${args[0].slice(0, 40)}' ${args[1]}`);
    return reply(lines.length ? lines.join('') : 'Nenhuma correspondência.');
  }
  decode(args) {
    if (args.length < 2) return reply('Uso: decode b64|hex <texto>', 'error');
    const kind = args[0].toLowerCase(), token = args.slice(1).join(' ');
    let bytes;
    try {
      if (kind === 'b64' || kind === 'base64') {
        // Formato estrito, como Base64.strict_decode64 do Ruby.
        if (!/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(token)) throw new Error('base64 inválido');
        bytes = Uint8Array.from(atob(token), c => c.charCodeAt(0));
        
      } else if (kind === 'hex') {
        const raw = token.replaceAll(' ', '');
        if (!/^(?:[0-9a-fA-F]{2})*$/.test(raw)) throw new Error('hex inválido');
        bytes = Uint8Array.from(raw.match(/.{2}/g) ?? [], pair => parseInt(pair, 16));
      } else return reply('Formato aceito: b64 ou hex.', 'error');
    } catch {return reply('Codificação inválida.', 'error');}
    if (bytes.byteLength > 4096) return reply('Entrada excede o limite de 4096 bytes.', 'error');
    let value;
    try {
      const decoded = new TextDecoder('utf-8', {fatal:true}).decode(bytes);
      value = [...decoded].every(c => c === '\n' || c === '\r' || (c.codePointAt(0) >= 32 && c.codePointAt(0) !== 127))
        ? decoded : Array.from(bytes, b=>b.toString(16).padStart(2,'0')).join('');
    } catch {value = Array.from(bytes, b=>b.toString(16).padStart(2,'0')).join('');}
    this.addJournal(`DECODE ${kind}`);
    return reply(`Resultado: ${value}`, 'success');
  }
  async hash(args) {
    if (args.length < 2 || args[0].toLowerCase() !== 'sha256') return reply('Uso: hash sha256 <texto>', 'error');
    const text = args.slice(1).join(' ');
    const encoded = new TextEncoder().encode(text);
    if (encoded.byteLength > 4096) return reply('Texto longo demais (máximo 4096 bytes).', 'error');
    try {
      const digest = new Uint8Array(await crypto.subtle.digest('SHA-256', encoded));
      return reply(`SHA-256: ${Array.from(digest, b => b.toString(16).padStart(2,'0')).join('')}`);
    } catch {return reply('SHA-256 não disponível neste navegador.', 'error');}
  }
  contain(args) {
    if (args.length !== 1) return reply('Uso: contain <IP>', 'error');
    if (this.missionIndex !== 2) return reply('Comando disponível apenas na missão 03.', 'error');
    if (!this.state.session || this.state.session.host !== '10.77.0.44' || this.state.session.port !== 8443) return reply('Acesse primeiro o console SEC-CTRL:8443.', 'error');
    if (args[0] !== '10.77.0.12') return reply('Este host não está autorizado no runbook. Nenhuma ação executada.', 'error');
    if (this.state.contained) return reply('WEB-01 já está isolado.');
    this.state.contained = true;
    this.addJournal('CONTAIN WEB-01 (somente simulação)');
    return reply('WEB-01 ISOLADO. Segmentação aplicada ao cenário fictício. Agora registre o ticket.', 'success');
  }
  submit(args) {
    if (!args.length) return reply('Uso: submit <resposta>', 'error');
    const answer = args.join(' ').trim();
    if (answer.toLowerCase() !== this.mission.answer.toLowerCase()) {
      this.state.penalty = Math.min(this.state.penalty + 5, 100);
      this.addJournal('SUBMIT incorreto (-5 pts)');
      return reply('Resposta não confere com as evidências. -5 pontos nesta missão.', 'error');
    }
    if (this.missionIndex === 2 && !this.state.contained) return reply('Antes de registrar o ticket, isole WEB-01 pelo console SEC-CTRL.', 'error');
    const points = Math.max(100 - this.state.penalty, 0);
    const name = this.mission.title, outro = this.mission.outro;
    this.state.score += points;
    this.addJournal(`COMPLETE ${name} +${points}`);
    this.state.mission_index++;
    this.state.penalty = 0;
    this.state.hint_used = false;
    this.state.contained = false;
    this.state.scanned = [];
    this.state.session = null;
    if (!this.complete) return reply(`✓ ${outro}\n+${points} pontos | TOTAL ${this.score}/300\n\n${this.intro}`, 'success');
    return reply(`✓ ${outro}\nMISSÃO FINALIZADA: ${name}\n+${points} pontos | TOTAL ${this.score}/300\n\n${this.ending()}`, 'win');
  }
  ending() {
    return `╔══════════════════════════════════════════════════╗\n║           OPERAÇÃO NEXUS: CONCLUÍDA             ║\n╚══════════════════════════════════════════════════╝\nPONTUAÇÃO: ${this.score}/300 | PATENTE: ${this.rank}\nA ameaça foi descoberta, atribuída e contida.\nO melhor ataque? Às vezes, é uma boa investigação.\nDigite status para conferir ou novo para recomeçar.\n`;
  }
  hint() {
    if (!this.state.hint_used) {this.state.penalty = Math.min(this.state.penalty + 15, 100); this.state.hint_used = true;}
    return reply(`DICA: ${this.mission.hint}\n(Penalidade total nesta missão: -${this.state.penalty})`);
  }
  journal() {
    const entries = this.state.journal.slice(-15);
    return reply(entries.length ? `DIÁRIO DE OPERAÇÕES\n${entries.map((e,i) => `${String(i+1).padStart(2,' ')}. ${e}`).join('\n')}` : 'Diário ainda vazio.');
  }
  help() {
    return reply(`COMANDOS DO TERMINAL (todos simulados)\n  help                       Mostra esta referência\n  map                        Mapa dos hosts do laboratório\n  scan <IP>                  Descobre serviços de um host fictício\n  connect <IP>:<porta>       Abre console do serviço\n  disconnect                 Encerra sessão atual\n  ls                         Lista arquivos do serviço\n  cat <arquivo>              Lê um arquivo\n  grep <texto> <arquivo>     Filtra linhas de um arquivo\n  decode b64 <texto>         Decodifica Base64\n  decode hex <texto>         Decodifica hexadecimal\n  hash sha256 <texto>        Calcula hash local\n  contain <IP>               Isola host virtual (na missão 03)\n  submit <resposta>          Entrega a solução da missão\n  hint                       Dica (-15 pontos na primeira vez)\n  status                     Mostra andamento/pontuação\n  journal                    Histórico recente de evidências\n  save                       Salva progresso\n  novo                       Reinicia toda a campanha\n  sair                       Salva e encerra\nDICA: espaços em argumentos? Use aspas, como grep "event_id=E-441" auth.log.\n`);
  }
  async perform(line) {
    let args;
    try {args = splitShellWords(String(line ?? '').trim());}
    catch (e) {return reply(`Entrada inválida: ${e.message === 'aspas não fechadas' ? 'Unmatched quote: ' + JSON.stringify(String(line ?? '').trim()) : e.message}`, 'error');}
    if (!args.length) return reply('Digite help para ver os comandos.');
    const command = args.shift().toLowerCase();
    if (command === 'novo') return this.reset();
    if (['sair','exit','quit'].includes(command)) return reply('Fim de transmissão. O estado foi salvo.', 'quit');
    if (this.complete && !['help','ajuda','status','journal','diario','save','salvar'].includes(command)) return reply('Comando indisponível após a conclusão. Use status, journal ou novo.');
    switch (command) {
      case 'help': case 'ajuda': return this.help();
      case 'map': case 'mapa': return this.map();
      case 'scan': return this.scan(args);
      case 'connect': return this.connect(args);
      case 'disconnect': case 'dc': return this.disconnect();
      case 'ls': case 'dir': return this.ls();
      case 'cat': return this.cat(args);
      case 'grep': return this.grep(args);
      case 'decode': return this.decode(args);
      case 'hash': return this.hash(args);
      case 'contain': return this.contain(args);
      case 'submit': return this.submit(args);
      case 'hint': case 'dica': return this.hint();
      case 'status': return this.status();
      case 'journal': case 'diario': return this.journal();
      case 'save': case 'salvar': return reply('Progresso registrado neste navegador.', 'success');
      default: return reply(`Comando desconhecido: ${command}. Digite help.`, 'error');
    }
  }
}
