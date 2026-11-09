"use strict";
// EXP-002: deliberately bounded educational SHA-256 Proof-of-Work worker.
// Canonical serialization: JSON.stringify([index, previousHash, data, difficulty, nonce]).
const encoder = new TextEncoder();
const MAX_ATTEMPTS = 500000;
function hex(bytes) { return Array.from(new Uint8Array(bytes), b => b.toString(16).padStart(2, "0")).join(""); }
async function digest(s) { return hex(await crypto.subtle.digest("SHA-256", encoder.encode(s))); }
self.onmessage = async (event) => {
  const x = event.data;
  if (!x || x.type !== "mine" || !Number.isInteger(x.index) || x.index < 1 || x.index > 5 ||
      !Number.isInteger(x.difficulty) || x.difficulty < 1 || x.difficulty > 4 ||
      typeof x.data !== "string" || x.data.length > 140 ||
      typeof x.previousHash !== "string" || !/^[0-9a-f]{64}$/.test(x.previousHash)) {
    self.postMessage({ type: "error", message: "Parâmetros de mineração inválidos." });
    return;
  }
  const start = performance.now();
  const target = "0".repeat(x.difficulty);
  try {
    for (let nonce = 0; nonce < MAX_ATTEMPTS; nonce++) {
      const hash = await digest(JSON.stringify([x.index, x.previousHash, x.data, x.difficulty, nonce]));
      const attempts = nonce + 1;
      if (hash.startsWith(target)) {
        self.postMessage({ type: "found", block: { index:x.index, previousHash:x.previousHash, data:x.data, difficulty:x.difficulty, nonce, hash }, attempts, elapsedMs:performance.now()-start });
        return;
      }
      if (attempts % 2500 === 0) {
        self.postMessage({ type: "progress", attempts, elapsedMs:performance.now()-start });
      }
    }
    self.postMessage({ type: "exhausted", attempts:MAX_ATTEMPTS, elapsedMs:performance.now()-start });
  } catch (_) {
    self.postMessage({ type: "error", message: "SHA-256 indisponível: verifique o navegador e HTTPS." });
  }
};
