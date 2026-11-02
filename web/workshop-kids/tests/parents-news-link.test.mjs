import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

const script=fs.readFileSync(new URL("../worker.js",import.meta.url),"utf8");
const target="https://workshop-news.pages.dev/#workshop";
for(const name of ["HTML","GAME_HTML","HEART_HTML"]){
  test(name+" direciona o aviso para pais à seção da Workshop News",()=>{
    const match=script.match(new RegExp("^const "+name+" = (.+);$","m"));
    assert.ok(match,"Página "+name+" está no Worker");
    const html=JSON.parse(match[1]);
    assert.ok(html.includes('href="'+target+'"'),"Link oficial presente");
    assert.equal(html.split(target).length-1,1,"Apenas uma ocorrência no aviso");
    assert.match(html,/rel="noopener noreferrer"/);
  });
}
