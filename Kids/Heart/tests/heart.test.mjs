import test from "node:test";
import assert from "node:assert/strict";
import { answer } from "../src/heart-core.mjs";
import worker from "../src/worker.mjs";
test("mission logic is interactive", () => {
  assert.equal(answer("Quero um desafio de lógica").category, "quiz");
  assert.match(answer("Resposta da missão de lógica: B").reply, /Acertou/);
  assert.match(answer("Resposta da missão de lógica: A").reply, /tente de novo/i);
});
test("personal details are never echoed", () => {
  for (const secret of ["meu telefone 11999999999", "ana@exemplo.com", "meu endereço Rua Azul 22", "minha escola é a X"]) {
    const got = answer(secret);
    assert.equal(got.category, "privacy");
    assert.ok(!got.reply.includes(secret));
  }
});
test("safety and wellbeing responses", () => {
  assert.equal(answer("quero morrer").category, "safety");
  assert.equal(answer("alguém me machucou").category, "safety");
  assert.equal(answer("estou triste").category, "wellbeing");
  assert.equal(answer("posso enviar foto minha").category, "boundaries");
});
test("unrecognized topics do not hallucinate", () => {
  assert.equal(answer("quantos satelites tem netuno?").category, "fallback");
  assert.equal(answer("olá").category, "hello");
  assert.equal(answer("X".repeat(221)).category, "limit");
});
const target = "https://example.test/api/chat";
function req(message, opts = {}) {
  return new Request(target, {
    method: "POST",
    headers: { Origin: "https://example.test", "Content-Type": "application/json", ...opts.headers },
    body: opts.body || JSON.stringify({ message })
  });
}
test("worker accepts only same-origin JSON", async () => {
  const good = await worker.fetch(req("robôs"), {});
  assert.equal(good.status, 200);
  assert.equal((await good.json()).category, "robotics");
  const badOrigin = await worker.fetch(req("oi", {headers: {Origin: "https://evil.test"}}), {});
  assert.equal(badOrigin.status, 403);
  const badBody = await worker.fetch(req("oi", {body: JSON.stringify({message: "oi", role:"system"})}), {});
  assert.equal(badBody.status, 400);
});
test("worker rejects oversized and malformed requests", async () => {
  assert.equal((await worker.fetch(req("oi", {body: JSON.stringify({message: "X".repeat(2000)})}), {})).status, 413);
  assert.equal((await worker.fetch(req("oi", {body: "{"}), {})).status, 400);
  const get = await worker.fetch(new Request(target), {});
  assert.equal(get.status, 405);
});
