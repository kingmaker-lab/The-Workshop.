import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

const source=fs.readFileSync(new URL("../worker.js",import.meta.url),"utf8")
 .replace(/export default \{ fetch\(request,env\)\{return respond\(request,env\);\} \};\s*$/,"");
const ctx=vm.createContext({Request,Response,URL,TextDecoder,Uint8Array,atob,addEventListener(){}});
vm.runInContext(source,ctx,{timeout:12000});
const origin="https://workshop-kids.example";
const route=(path,method="GET")=>ctx.respond(new Request(origin+path,{method}));
const content=name=>vm.runInContext(name,ctx);
const engine=(name,names)=>{
 const s=content(name),begin=s.indexOf("/* ENGINE START */"),end=s.indexOf("/* ENGINE END */");
 assert.ok(begin>=0&&end>begin,name+" engine markers");
 const part=s.slice(begin+"/* ENGINE START */".length,end);
 return new Function(part+"; return {"+names.join(",")+"};")();
};

test("Portal e três novos jogos possuem rotas, assets e metadados corretos",async()=>{
 const routes=[
 ["/jogos/","Game Lab"],["/jogos/robot-factory/","Robot Factory"],
 ["/jogos/cyber-guardian/","Cyber Guardian"],["/jogos/mini-circuit/","Mini Circuit Lab"]
 ];
 const home=await route("/").text();
 for(const [path,title] of routes){
  const res=route(path);
  assert.equal(res.status,200,path);
  assert.match(res.headers.get("Content-Type"),/text\/html/);
  assert.ok((await res.text()).includes(title),path+" title");
  assert.match(res.headers.get("Content-Security-Policy"),/connect-src 'none'/);
  assert.ok(home.includes('href="'+path+'"'),"link do jogo "+path);
  const head=route(path,"HEAD");
  assert.equal(head.status,200);
  assert.equal(await head.text(),"");
  assert.equal(route(path,"POST").status,405);
  assert.equal(route(path+"index.html").status,200);
  assert.equal(route(path.slice(0,-1)).status,200);
 }
 for(const path of ["/jogos/games.css","/jogos/robot.js","/jogos/guardian.js","/jogos/circuit.js"]){
  assert.equal(route(path).status,200,path);
  assert.equal(route(path,"POST").status,405);
 }
 assert.equal(route("/jogos/inexistente/").status,404);
});
test("Códigos dos jogos são locais, sem coleta ou rede",()=>{
 for(const n of ["ROBOT_JS","GUARDIAN_JS","CIRCUIT_JS"]){
  const js=content(n);
  assert.doesNotMatch(js,/\bfetch\s*\(|localStorage|sessionStorage|document\.cookie|\.innerHTML\s*=|\beval\s*\(/);
  assert.doesNotThrow(()=>new Function(js));
 }
 const catalog=content("KIDS_GAMES_HTML");
 assert.ok(catalog.includes("/assets/heart.webp?v=00ff52e6"));
 assert.ok(catalog.includes("/assets/blade.webp?v=e04bfb99"));
 for(const n of ["ROBOT_HTML","GUARDIAN_HTML","CIRCUIT_HTML"]){
  const html=content(n);
  assert.ok(html.includes("https://workshop-news.pages.dev/#workshop"));
  assert.match(html,/role="status"/);
 }
});
test("Heart's Robot Factory: quatro missões solucionáveis e obstáculos funcionais",()=>{
 const {RF_LEVELS,robotSim}=engine("ROBOT_JS",["RF_LEVELS","robotSim"]);
 const solutions=[
  ["F","F","P","F"],
  ["L","F","F","R","F","F","P","F"],
  ["F","I","R2","I","F"],
  ["R2","I","R2","L","R2","I","R2"]
 ];
 assert.equal(RF_LEVELS.length,4);
 RF_LEVELS.forEach((lev,i)=>assert.equal(robotSim(lev,solutions[i]).status,"win","factory "+(i+1)));
 assert.equal(robotSim(RF_LEVELS[1],["F"]).status,"wall");
 assert.equal(robotSim(RF_LEVELS[0],["F","F","F"]).status,"parts");
 assert.equal(robotSim(RF_LEVELS[0],["P"]).status,"no-part");
 assert.equal(robotSim(RF_LEVELS[2],["F","P","R2","P","F"]).status,"condition");
 assert.equal(robotSim(RF_LEVELS[3],["F","F","I","F","F","L","F","F","I","F","F"]).status,"repeat");
 assert.equal(robotSim(RF_LEVELS[0],[]).status,"empty");
});
test("Blade: cinco situações educativas com respostas e tentativas",()=>{
 const {CG_CASES,guardianJudge}=engine("GUARDIAN_JS",["CG_CASES","guardianJudge"]);
 assert.equal(CG_CASES.length,5);
 for(const scenario of CG_CASES){
  assert.equal(scenario.options.length,3);
  assert.equal(guardianJudge(scenario,scenario.answer).status,"correct");
  assert.equal(guardianJudge(scenario,(scenario.answer+1)%3).status,"retry");
  assert.ok(scenario.reason.length>20);
  assert.doesNotMatch(scenario.situation,/https?:\/\//);
 }
 assert.equal(guardianJudge(CG_CASES[0],99).status,"invalid");
});
test("Mini Circuit Lab: eletricidade aproximada com resguardo de polaridade e resistor",()=>{
 const {CL_LEVELS,circuitSim}=engine("CIRCUIT_JS",["CL_LEVELS","circuitSim"]);
 assert.equal(CL_LEVELS.length,3);
 const base={battery:3,resistor:220,leds:1,direction:"forward",switch:"closed"};
 assert.equal(circuitSim(base,CL_LEVELS[0]).status,"win");
 assert.equal(circuitSim({...base,direction:"reverse"},CL_LEVELS[1]).status,"reverse");
 assert.equal(circuitSim({...base,switch:"open"},CL_LEVELS[0]).status,"open");
 assert.equal(circuitSim({...base,resistor:0},CL_LEVELS[0]).status,"resistor");
 assert.equal(circuitSim({...base,battery:3,leds:2},CL_LEVELS[2]).status,"voltage");
 assert.equal(circuitSim({...base,battery:5,leds:2},CL_LEVELS[2]).status,"win");
 const result=circuitSim({...base,battery:5,leds:2},CL_LEVELS[2]);
 assert.equal(result.lit,true);
 assert.ok(result.mA>5&&result.mA<6);
 assert.equal(circuitSim({...base,leds:2},CL_LEVELS[0]).status,"voltage");
});
test("Chats existentes e rate limiting continuam presentes",()=>{
 assert.equal(route("/heart/").status,200);
 assert.equal(route("/blade/conversar/").status,200);
 assert.equal(route("/jogar/").status,200);
 assert.match(source,/KIDS_API_LIMITER/);
 assert.match(source,/KIDS_AI_LIMITER/);
 assert.match(content("HEART_PROMPT"),/Você é a Heart, uma lobinha/);
 assert.match(content("HTML"),/href="\/jogos\/"/);
});
