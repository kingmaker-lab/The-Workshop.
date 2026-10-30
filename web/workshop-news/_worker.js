// Workshop News: additive ARGUS route on top of the immutable last known-good release.
// The upstream URL is deliberately pinned. It must never be derived from user input.
const PREVIOUS_DEPLOYMENT = "https://aae8ce82.workshop-news.pages.dev";
const ARTICLE = `<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#080f17"><meta name="description" content="ARGUS v0.2: atualização do laboratório defensivo open source The Workshop."><title>ARGUS v0.2 | Workshop News</title><style>:root{color-scheme:dark;--bg:#080f17;--card:#111f2a;--line:#28414a;--text:#e8f5f2;--muted:#adc1c1;--a:#b9eb75;font:15px/1.75 system-ui,sans-serif}*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 80% 0%,#182e36,transparent 45%),var(--bg);color:var(--text)}a{color:var(--a)}header,main,footer{max-width:900px;padding:0 24px;margin:auto}header{padding-top:25px;padding-bottom:24px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;gap:18px;flex-wrap:wrap;font:700 12px ui-monospace,monospace}main{padding-top:72px;padding-bottom:72px}.overline{font:700 12px ui-monospace,monospace;letter-spacing:.13em;color:var(--a)}h1{font-size:clamp(42px,8vw,84px);line-height:1.08;letter-spacing:-.05em;margin:20px 0}.lede{font-size:21px;color:var(--muted)}.grid{display:grid;grid-template-columns:1fr 1fr;gap:15px;margin:30px 0}.card{padding:24px;border:1px solid var(--line);background:var(--card);border-radius:12px}.card strong{color:var(--a)}.card p,.note{color:var(--muted)}.links{display:flex;flex-wrap:wrap;gap:10px;margin:35px 0}.links a{display:inline-block;padding:12px 17px;border:1px solid var(--a);text-decoration:none;font-weight:700;font-size:13px}.links a:first-child{background:var(--a);color:#091115}.notice{border-left:3px solid var(--a);padding:16px 20px;background:var(--card)}footer{border-top:1px solid var(--line);padding-top:22px;padding-bottom:30px;color:var(--muted);font:12px ui-monospace,monospace}@media(max-width:700px){.grid{grid-template-columns:1fr}main{padding-top:45px}}</style></head><body><header><a href="/">THE WORKSHOP / NEWS</a><a href="https://workshop-labs.pages.dev/argus/">ARGUS LAB ↗</a></header><main><div class="overline">30.10.2026 / LAB UPDATE / THREAT HUNTING</div><h1>ARGUS v0.2: do ruído ao sinal.</h1><p class="lede">O laboratório defensivo do The Workshop ganhou uma camada experimental de detecção de anomalias estatísticas em telemetria de rede, integrada ao motor local de correlação e score de risco.</p><div class="grid"><section class="card"><strong>ANÁLISE ESTATÍSTICA</strong><h2>Welford online</h2><p>Uma baseline por fonte e métrica, com aquecimento configurável. Desvios numéricos podem gerar alertas auditáveis.</p></section><section class="card"><strong>VALIDAÇÃO</strong><h2>17 testes aprovados</h2><p>Regressões para processamento, API local e anomalias. Publicação de código aprovada pelo CI.</p></section><section class="card"><strong>TELEMETRIA</strong><h2>JSONL, Syslog, Zeek</h2><p>O motor coleta eventos de arquivos locais, normaliza entradas e correlaciona sequências por IP.</p></section><section class="card"><strong>GOVERNANÇA</strong><h2>Local first</h2><p>O detector novo é desativado por padrão. Nada é enviado dos seus computadores ao portal.</p></section></div><div class="notice"><strong>Nota de pesquisa:</strong> uma anomalia é uma hipótese, não uma condenação. Baselines podem apresentar falsos positivos, drift e contaminação. Esta versão é experimental e não substitui investigação humana.</div><div class="links"><a href="https://workshop-labs.pages.dev/argus/">EXPLORAR ARGUS ↗</a><a href="https://github.com/kingmaker-lab/The-Workshop./tree/main/argus" rel="noopener noreferrer">REPOSITÓRIO ↗</a><a href="https://github.com/kingmaker-lab/The-Workshop./pull/16" rel="noopener noreferrer">EVIDÊNCIAS ↗</a></div></main><footer>© 2026 THE WORKSHOP / KINGMAKER LAB · BUILD. BREAK. UNDERSTAND. REBUILD.</footer></body></html>`;

const HARDENING = {
  "x-content-type-options": "nosniff",
  "x-frame-options": "DENY",
  "referrer-policy": "no-referrer",
  "permissions-policy": "camera=(), microphone=(), geolocation=()",
};
const ARTICLE_HEADERS = {
  "content-type": "text/html; charset=utf-8",
  "cache-control": "public, max-age=120",
  "content-security-policy": "default-src 'none'; script-src 'none'; style-src 'unsafe-inline'; img-src 'none'; connect-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
  ...HARDENING,
};

function argusCard() {
  return '<a href="/argus/" class="lab-entry"><span class="lab-icon">◉</span><span><strong>ARGUS v0.2</strong><small>Threat hunting local / detecção experimental</small></span><b>↗</b></a>';
}

export default {
  async fetch(request) {
    const method = request.method;
    if (!["GET", "HEAD"].includes(method)) {
      return new Response("Method Not Allowed", {status: 405, headers: {"allow": "GET, HEAD", ...HARDENING, "cache-control": "no-store"}});
    }
    const url = new URL(request.url);
    const path = url.pathname;
    if (path === "/argus" || path === "/argus/" || path === "/argus/index.html") {
      return new Response(method === "HEAD" ? null : ARTICLE, {status: 200, headers: ARTICLE_HEADERS});
    }
    if (path.startsWith("//")) {
      return new Response("Bad Request", {status: 400, headers: HARDENING});
    }

    const destination = new URL(PREVIOUS_DEPLOYMENT);
    destination.pathname = path;
    destination.search = url.search;

    try {
      const response = await fetch(destination, {
        method,
        headers: {"accept": request.headers.get("accept") || "*/*"},
        redirect: "manual",
      });
      const headers = new Headers(response.headers);
      headers.delete("set-cookie");
      headers.delete("content-length");
      headers.set("x-content-type-options", "nosniff");
      headers.set("referrer-policy", "no-referrer");

      if (method === "HEAD") {
        return new Response(null, {status: response.status, headers});
      }
      if ((path === "/" || path === "/index.html") && response.ok &&
          (headers.get("content-type") || "").includes("text/html")) {
        let html = await response.text();
        const marker = '<div class="lab-links">';
        if (html.includes(marker) && !html.includes('href="/argus/"')) {
          html = html.replace(marker, marker + argusCard())
            .replace('<span class="tiny">/ 04</span>', '<span class="tiny">/ 05</span>');
        }
        return new Response(html, {status: response.status, headers});
      }
      return new Response(response.body, {status: response.status, headers});
    } catch {
      return new Response("News origin temporarily unavailable", {
        status: 502,
        headers: {"content-type": "text/plain; charset=utf-8", "cache-control": "no-store", ...HARDENING},
      });
    }
  }
};
