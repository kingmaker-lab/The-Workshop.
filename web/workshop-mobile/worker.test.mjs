import test from "node:test";
import assert from "node:assert/strict";
import portal from "./worker.mjs";

const make = path => new Request("https://example.org" + path);
const orig = globalThis.fetch;
const requestRelease = async () => {
  const r = await portal.fetch(make("/api/release"));
  assert.equal(r.status, 200);
  return r.json();
};

test("portal html renderiza e download inicialmente bloqueado", async () => {
  const r = await portal.fetch(make("/"));
  assert.equal(r.status, 200);
  assert.match(r.headers.get("content-security-policy"), /script-src 'self'/);
  const body = await r.text();
  assert.match(body, /Wolfpack Academy/);
  assert.match(body, /APK assinado indisponível/);
});

test("página fornece javascript e health", async () => {
  const js = await portal.fetch(make("/client.js"));
  assert.equal(js.status, 200);
  assert.match(await js.text(), /SHA-256|sha256/);
  const health = await portal.fetch(make("/health"));
  assert.deepEqual(await health.json(), {ok:true,site:"workshop-mobile"});
});

test("métodos e rotas não autorizadas bloqueados", async () => {
  assert.equal((await portal.fetch(new Request("https://example.org/",{method:"POST"}))).status,405);
  assert.equal((await portal.fetch(make("/unknown"))).status,404);
});

test("release indisponível se não houver versão assinada", async () => {
  globalThis.fetch = async () => new Response(JSON.stringify([{tag_name:"other-v2.0.0",draft:false,prerelease:false,assets:[]}]),{status:200});
  try {assert.deepEqual(await requestRelease(),{available:false});}
  finally {globalThis.fetch=orig;}
});

test("release com APK, URL exata e digest sha256 aparece", async () => {
  const tag="wolfpack-academy-v0.2.0";
  const asset={name:tag+".apk",size:12345,digest:"sha256:"+"a".repeat(64),
    browser_download_url:"https://github.com/kingmaker-lab/The-Workshop./releases/download/"+tag+"/"+tag+".apk"};
  globalThis.fetch=async()=>new Response(JSON.stringify([{tag_name:tag,draft:false,prerelease:false,assets:[asset]}]),{status:200});
  try {
    const r=await requestRelease();
    assert.equal(r.available,true);
    assert.equal(r.sha256,"a".repeat(64));
    assert.equal(r.url,asset.browser_download_url);
  }finally{globalThis.fetch=orig;}
});

test("release sem digest, com url falsa ou draft não é oferecido",async()=>{
  const tag="wolfpack-academy-v0.2.0";
  const item={tag_name:tag,draft:false,prerelease:false,assets:[{name:tag+".apk",size:12,digest:"sha256:"+"b".repeat(64),browser_download_url:"https://example.net/bad.apk"}]};
  globalThis.fetch=async()=>new Response(JSON.stringify([item]),{status:200});
  try{assert.equal((await requestRelease()).available,false);}finally{globalThis.fetch=orig;}
  item.assets[0].browser_download_url="https://github.com/kingmaker-lab/The-Workshop./releases/download/"+tag+"/"+tag+".apk";
  delete item.assets[0].digest;
  globalThis.fetch=async()=>new Response(JSON.stringify([item]),{status:200});
  try{assert.equal((await requestRelease()).available,false);}finally{globalThis.fetch=orig;}
  item.draft=true;
  item.assets[0].digest="sha256:"+"b".repeat(64);
  globalThis.fetch=async()=>new Response(JSON.stringify([item]),{status:200});
  try{assert.equal((await requestRelease()).available,false);}finally{globalThis.fetch=orig;}
});
