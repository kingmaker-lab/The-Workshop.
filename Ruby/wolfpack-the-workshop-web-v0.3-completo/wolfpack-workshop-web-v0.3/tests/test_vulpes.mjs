import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import {VulpesGame,splitShellWords} from '../js/vulpes-engine.js';
import {DATA} from '../js/vulpes-data.js';
const root = dirname(fileURLToPath(import.meta.url));
const scenarios = [
  ['help','map','scan 10.77.0.12','connect 10.77.0.12:80','ls','cat index.html','disconnect','connect 10.77.0.12:8080','scan 10.77.0.12','connect 10.77.0.12:8080','ls','cat readme.txt','cat traffic.log','decode b64 TklHSFRKQVI=','decode hex 464f58','hash sha256 abc','submit NIGHTJAR','status','map','scan 10.77.0.23','connect 10.77.0.23:9200','ls','cat egress.log','grep E-441 auth.log','submit svc-bridge','scan 10.77.0.44','connect 10.77.0.44:8443','cat runbook.txt','cat incident.json','submit IR-2607','contain 10.77.0.23','contain 10.77.0.12','submit IR-2607','status','map','journal','help','save','novo','status'],
  ['map','scan 8.8.8.8','connect 8.8.8.8:53','scan 10.77.0.44','connect 10.77.0.12:8080','ls','cat nope','grep abc auth.log','decode b64 !!!','decode hex ZZZ','hash sha256','scan localhost','$(touch /tmp/exploit)','hint','hint','submit wrong','status','submit NIGHTJAR','status','journal'],
  ['scan 10.77.0.1','connect 10.77.0.1:53','cat zones.txt','grep "log-01.lab" zones.txt','disconnect','scan 10.77.0.12','connect 10.77.0.12:8080','cat notes.txt','decode hex 48 69','decode b64 TklHSFRKQVI=','submit nightjar','scan 10.77.0.23','connect 10.77.0.23:9200','grep "event_id=E-441" auth.log','submit SVC-BRIDGE','scan 10.77.0.44','connect 10.77.0.44:8443','cat dashboard.txt','contain 10.77.0.1','contain 10.77.0.12','contain 10.77.0.12','submit ir-2607'],
  ['novo','ajuda','mapa','dica','salvar','diario','sair','status','novo','status'],
  ['connect "bad','scan','connect','decode','grep','cat','hash nope abc','submit','contain','dir','dc','exit']
];
let runs = 0;
for (const scenario of scenarios) {
  const out = spawnSync('ruby', [join(root,'vulpes_ruby_reference.rb')], {input:JSON.stringify(scenario),encoding:'utf8'});
  if (out.status !== 0) throw new Error(`Ruby falhou: ${out.stderr}`);
  const expected = JSON.parse(out.stdout);
  const game = new VulpesGame();
  for (let i=0; i<scenario.length; i++) {
    const actual = await game.perform(scenario[i]);
    const want = expected[i];
    assert.equal(actual.kind,want.kind,`kind: ${scenario[i]}`);
    assert.equal(actual.text, ['save','salvar'].includes(scenario[i]) ? 'Progresso registrado neste navegador.' : want.text,`texto: ${scenario[i]}`);
    assert.equal(game.score,want.score,`score: ${scenario[i]}`);
    assert.equal(game.missionIndex,want.mission_index,`etapa: ${scenario[i]}`);
    runs++;
  }
}
assert.equal(DATA.version,'0.1.0');
assert.equal(DATA.missions.length,3);
assert.equal(DATA.files['10.77.0.12:8080']['traffic.log'].includes('TklHSFRKQVI='),true);
assert.deepEqual(splitShellWords('grep "event_id=E-441" auth.log'),['grep','event_id=E-441','auth.log']);
const stateGame = new VulpesGame();
await stateGame.perform('scan 10.77.0.12');
await stateGame.perform('connect 10.77.0.12:8080');
let restored = new VulpesGame(stateGame.snapshot());
assert.equal(restored.prompt,'vulpes77@WEB-01:8080$ ');
assert.equal((await restored.perform('ls')).text.includes('traffic.log'),true);
assert.equal(new VulpesGame({...stateGame.snapshot(),mission_index:77}).missionIndex,0);
assert.equal(new VulpesGame({...stateGame.snapshot(),session:{host:'8.8.8.8',port:53}}).state.session,null);
console.log(`✓ VULPES-77: ${runs} comandos comparados com motor Ruby original; save e sanitização validados.`);
