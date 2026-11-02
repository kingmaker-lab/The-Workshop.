import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

const worker = fs.readFileSync(new URL("../worker.js", import.meta.url), "utf8").replace(/export default \{ fetch\(request,env\)\{return respond\(request,env\);\} \};\s*$/, "");
const ctx = vm.createContext({ Request, Response, URL, addEventListener() {} });
vm.runInContext(worker, ctx, { timeout: 5000 });

function serve(path, method = "GET") {
  return ctx.respond(new Request("https://workshop-kids.example" + path, { method }));
}
const gameClient = vm.runInContext("GAME_JS", ctx);
const gameHTML = vm.runInContext("GAME_HTML", ctx);
const gameCSS = vm.runInContext("GAME_CSS", ctx);
const start = gameClient.indexOf("const DIRECTIONS=");
const end = gameClient.indexOf("const LEVELS=");
assert.ok(start !== -1 && end > start, "engine presente");
const core = gameClient.slice(start, end);
const check = new Function(core + "; return {expandProgram, checkProgram}")();
const json = gameClient.match(/const LEVELS=(\[[^\n]+\]);\nconst \$=/);
assert.ok(json, "níveis embutidos no jogo");
const levels = JSON.parse(json[1]);

test("novo jogo e página inicial acessíveis por GET", async () => {
  const home = await serve("/").text();
  assert.match(home, /href="\/jogar\/"/);
  const res = serve("/jogar/");
  assert.equal(res.status, 200);
  assert.match(res.headers.get("Content-Type"), /text\/html/);
  assert.match(await res.text(), /Missão dos Algoritmos/);
  assert.equal(serve("/jogar").status, 200);
  assert.equal(serve("/jogar/index.html").status, 200);
});
test("assets próprios servidos e CSP sem rede para o cliente", async () => {
  assert.equal(await serve("/game.js").text(), gameClient);
  assert.equal(await serve("/game.css").text(), gameCSS);
  assert.ok(gameHTML.includes('src="/game.js"'));
  assert.ok(gameCSS.includes(".board"));
  assert.match(serve("/jogar/").headers.get("Content-Security-Policy"), /connect-src 'none'/);
  assert.equal(serve("/jogar/", "HEAD").status, 200);
  assert.equal(await serve("/jogar/", "HEAD").text(), "");
  assert.equal(serve("/jogar/", "POST").status, 405);
  assert.equal(serve("/nao-existe").status, 404);
  assert.doesNotMatch(gameClient, /\bfetch\s*\(|\blocalStorage\b|document\.cookie/);
});
test("5 fases possuem solução validada", () => {
  const solutions = [
    [{kind:"move",dir:"right"},{kind:"move",dir:"right"},{kind:"move",dir:"right"}],
    [{kind:"move",dir:"up"},{kind:"move",dir:"up"},{kind:"move",dir:"right"},{kind:"move",dir:"right"}],
    [{kind:"repeat",dir:"right",times:4}],
    [{kind:"repeat",dir:"up",times:3},{kind:"repeat",dir:"right",times:4}],
    [{kind:"repeat",dir:"up",times:2},{kind:"repeat",dir:"right",times:2},{kind:"repeat",dir:"up",times:2},{kind:"repeat",dir:"right",times:2}]
  ];
  assert.equal(levels.length, 5);
  levels.forEach((level, i) => assert.equal(check.checkProgram(level, solutions[i]).status, "win", "fase "+(i+1)));
});
test("feedback de erros e prevenção de execuções excessivas", () => {
  assert.equal(check.checkProgram(levels[0], []).status, "empty");
  assert.equal(check.checkProgram(levels[0], [{kind:"move",dir:"left"}]).status, "edge");
  assert.equal(check.checkProgram(levels[1], [{kind:"move",dir:"right"}]).status, "wall");
  assert.equal(check.checkProgram(levels[2], Array.from({length:4},()=>({kind:"move",dir:"right"}))).status, "loop_needed");
  assert.equal(check.checkProgram(levels[0], Array.from({length:17},()=>({kind:"move",dir:"right"}))).status, "too_many");
  assert.equal(check.checkProgram(levels[0], [{kind:"repeat",dir:"left",times:9000}]).status, "invalid");
});
