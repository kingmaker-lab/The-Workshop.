import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { CATEGORIES, SERVICES } from "../catalog.mjs";
import { normalizePhone, whatsappUrl, buildWhatsAppMessage, formatBRL } from "../whatsapp.mjs";

test("catálogo tem IDs únicos, preços positivos e categorias válidas", () => {
  assert.equal(SERVICES.length, 16);
  assert.equal(new Set(SERVICES.map((x) => x.id)).size, SERVICES.length);
  const categories = new Set(CATEGORIES.filter((x) => x.id !== "all").map((x) => x.id));
  for (const item of SERVICES) {
    assert.ok(categories.has(item.category), item.id);
    assert.ok(Number.isFinite(item.price) && item.price > 0, item.id);
    assert.ok(item.title && item.description, item.id);
  }
});
test("WhatsApp só habilita número brasileiro internacional válido", () => {
  assert.equal(normalizePhone(""), null);
  assert.equal(normalizePhone("11 99999-9999"), null);
  assert.equal(normalizePhone("5511999999999"), "5511999999999");
  assert.equal(normalizePhone("+55 (11) 99999-9999"), "5511999999999");
  assert.equal(normalizePhone("55119abc"), null);
  assert.equal(whatsappUrl("", []), null);
});
test("link de orçamento preserva os serviços selecionados", () => {
  const selected = [SERVICES[0], SERVICES[11]];
  const url = whatsappUrl("5511999999999", selected);
  const parsed = new URL(url);
  assert.equal(parsed.origin, "https://wa.me");
  assert.equal(parsed.pathname, "/5511999999999");
  const message = parsed.searchParams.get("text");
  assert.match(message, /The Workshop Store/);
  assert.ok(message.includes(SERVICES[0].title));
  assert.ok(message.includes(SERVICES[11].title));
  assert.match(message, /mês/);
  assert.match(message, /preços apresentados são estimativas/);
});
test("mensagem vazia permite contato avulso e moeda brasileira", () => {
  assert.match(buildWhatsAppMessage([]), /projeto personalizado/);
  assert.match(formatBRL(149), /149/);
});
test("estática usa recursos locais e cabeçalhos de segurança", () => {
  const html = readFileSync(fileURLToPath(new URL("../index.html", import.meta.url)), "utf8");
  const headers = readFileSync(fileURLToPath(new URL("../_headers", import.meta.url)), "utf8");
  assert.match(html, /lang="pt-BR"/);
  assert.match(html, /type="module" src=".\/app.js"/);
  assert.match(headers, /Content-Security-Policy:/);
  assert.match(headers, /script-src 'self'/);
  assert.match(headers, /frame-ancestors 'none'/);
});
