import { answer } from "./heart-core.mjs";

const securityHeaders = {
  "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
  "Referrer-Policy": "no-referrer",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
  "Cross-Origin-Resource-Policy": "same-origin",
  "Cache-Control": "no-store"
};
function response(body, status = 200, type = "application/json; charset=utf-8") {
  return new Response(body, { status, headers: { ...securityHeaders, "Content-Type": type } });
}
function json(data, status = 200) { return response(JSON.stringify(data), status); }
async function readLimited(request, maximum = 1024) {
  if (!request.body) throw new Error("EMPTY");
  const reader = request.body.getReader();
  const chunks = [];
  let total = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    total += value.byteLength;
    if (total > maximum) {
      await reader.cancel();
      throw new Error("TOO_LARGE");
    }
    chunks.push(value);
  }
  const bytes = new Uint8Array(total);
  let offset = 0;
  for (const part of chunks) { bytes.set(part, offset); offset += part.byteLength; }
  return new TextDecoder("utf-8", { fatal: true }).decode(bytes);
}
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/api/chat") {
      if (request.method !== "POST") return json({ error: "method_not_allowed" }, 405);
      if (request.headers.get("Origin") !== url.origin) return json({ error: "forbidden_origin" }, 403);
      if (!/^application\/json(?:\s*;|$)/i.test(request.headers.get("Content-Type") || "")) {
        return json({ error: "unsupported_content_type" }, 415);
      }
      const length = Number(request.headers.get("Content-Length") || 0);
      if (length > 1024) return json({ error: "too_large" }, 413);
      let input;
      try {
        input = JSON.parse(await readLimited(request));
      } catch (error) {
        return json({ error: error.message === "TOO_LARGE" ? "too_large" : "invalid_json" },
          error.message === "TOO_LARGE" ? 413 : 400);
      }
      if (!input || typeof input !== "object" || Array.isArray(input) ||
          typeof input.message !== "string" || Object.keys(input).some((k) => k !== "message")) {
        return json({ error: "invalid_request" }, 400);
      }
      return json(answer(input.message));
    }
    if (request.method !== "GET" && request.method !== "HEAD") return response("Method not allowed", 405, "text/plain");
    if (!env?.ASSETS) return response("Asset binding unavailable", 503, "text/plain");
    const staticResponse = await env.ASSETS.fetch(request);
    const headers = new Headers(staticResponse.headers);
    for (const [name, value] of Object.entries(securityHeaders)) headers.set(name, value);
    return new Response(staticResponse.body, { status: staticResponse.status, headers });
  }
};
