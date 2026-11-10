/**
 * The Workshop Mobile — Worker independente.
 * Download é exibido somente após release GitHub com APK e digest SHA-256.
 * Não recebe credenciais nem dados pessoais.
 */
const REPO = "kingmaker-lab/The-Workshop.";
const RELEASES_API = "https://api.github.com/repos/" + REPO + "/releases?per_page=30";
const HEADERS = {
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "no-referrer",
  "X-Frame-Options": "DENY",
  "Cross-Origin-Resource-Policy": "same-origin",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=()"
};

const PAGE = String.raw`<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="theme-color" content="#071220">
  <meta name="description" content="The Workshop Mobile: aplicativos gratuitos para aprender, experimentar e desenvolver. Baixe a Wolfpack Academy para Android com verificação SHA-256.">
  <title>The Workshop Mobile | Wolfpack Academy</title>
  <style>
  :root{font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color-scheme:dark;--bg:#071220;--fg:#e8f6fc;--muted:#a1b5c6;--line:#234257;--cyan:#4ad9ed;--lime:#96e1c3}
  *{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;min-height:100vh;background:radial-gradient(ellipse at 78% 0%,#16425d 0,transparent 36%),radial-gradient(ellipse at 0% 52%,#121f3f 0,transparent 48%),var(--bg);color:var(--fg)}
  a{color:inherit}a:focus-visible,button:focus-visible{outline:3px solid var(--cyan);outline-offset:4px}
  .wrap{width:min(1080px,calc(100% - 34px));margin:auto}
  header{border-bottom:1px solid #2c4659a8;background:#071321a8;backdrop-filter:blur(9px)}
  nav{display:flex;align-items:center;justify-content:space-between;gap:15px;min-height:74px}
  .brand{text-decoration:none;font-weight:850;letter-spacing:.08em;display:flex;align-items:center;gap:12px;font-size:.94rem}.brand-mark{width:38px;height:38px;display:grid;place-items:center;border-radius:12px;background:#163c54;border:1px solid #3284a6;font-size:1.4rem}
  .navlinks{display:flex;gap:17px;color:#bed2df;font-size:.87rem}.navlinks a{text-decoration:none}
  .hero{padding:90px 0 62px;display:grid;grid-template-columns:minmax(0,1.35fr) minmax(270px,.75fr);gap:50px;align-items:center}
  .eyebrow{color:var(--cyan);font-weight:750;letter-spacing:.22em;text-transform:uppercase;font-size:.74rem}
  h1{font-weight:850;letter-spacing:-.055em;font-size:clamp(2.8rem,6.4vw,5.4rem);line-height:1.02;margin:17px 0 23px}
  h1 span{background:linear-gradient(90deg,#50e2f7,#a2e6d0);color:transparent;background-clip:text}
  .lead{color:#c0d6e3;font-size:1.12rem;line-height:1.75;max-width:660px}
  .pills{display:flex;gap:10px;flex-wrap:wrap;margin-top:25px}.pill{border:1px solid var(--line);border-radius:999px;padding:8px 12px;background:#12273b;color:#c7e0e9;font-size:.85rem}
  .phone{margin:auto;width:min(290px,100%);height:420px;border:7px solid #2a445b;border-radius:38px;box-shadow:0 20px 65px #0007,0 0 100px #1bbbd315;position:relative;background:linear-gradient(155deg,#16364d,#091627 64%);padding:30px 20px;transform:rotate(4deg)}
  .phone:before{content:"";position:absolute;top:9px;left:36%;width:28%;height:10px;border-radius:20px;background:#06101b}.screen-icon{font-size:3.4rem;display:block;margin:30px 0 10px}
  .phone small{letter-spacing:.18em;color:var(--cyan)}.phone h3{font-size:1.45rem;margin:12px 0 8px}.screen-card{padding:15px;background:#1e3d50;border:1px solid #325971;border-radius:14px;margin:15px 0;font-size:.85rem}.screen-meter{height:8px;border-radius:15px;background:linear-gradient(90deg,var(--cyan) 36%,#36556b 36%);margin-top:13px}
  section{padding:30px 0 55px}h2{font-size:clamp(1.8rem,4vw,2.6rem);margin:0 0 15px;letter-spacing:-.035em}p{line-height:1.7}
  .panel{border:1px solid #375467;background:linear-gradient(145deg,#102c40,#0b1b2e);border-radius:25px;padding:29px;box-shadow:0 15px 60px #0003}
  .tag{font-weight:700;font-size:.75rem;letter-spacing:.12em;color:var(--lime);text-transform:uppercase}
  .release-grid{display:grid;grid-template-columns:1fr auto;gap:24px;align-items:center}.release-grid .description{color:var(--muted);max-width:650px}
  .button{display:inline-flex;align-items:center;justify-content:center;text-decoration:none;border-radius:12px;background:var(--cyan);font-weight:800;color:#052233;min-height:53px;padding:0 25px;white-space:nowrap}
  .button[aria-disabled="true"]{background:#395266;color:#c5d6df;cursor:not-allowed}
  .digest{font: .85rem/1.65 ui-monospace,SFMono-Regular,Consolas,monospace;overflow-wrap:anywhere;color:#b9d4e4;background:#081727;border:1px solid #27475b;border-radius:12px;padding:14px 16px;margin-top:22px}
  .cards{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:25px}.card{border:1px solid #29485d;background:#0f2639;border-radius:20px;padding:22px}.card strong{display:block;font-size:1.08rem;margin-bottom:9px}.card p{color:var(--muted);font-size:.92rem;margin:0}.icon{font-size:1.7rem;margin-bottom:15px}
  .steps{padding-left:21px;color:#b7d0de;line-height:2}.steps li{padding-left:5px}code{color:#92eac8;font-family:ui-monospace,Consolas,monospace}.faint{color:var(--muted);font-size:.9rem}
  .footer{border-top:1px solid #223c4d;padding:28px 0 40px;color:#a0bacc;font-size:.85rem}
  @media(max-width:750px){.hero{grid-template-columns:1fr;padding-top:54px;gap:20px}.phone{height:280px;max-width:240px;transform:rotate(2deg);overflow:hidden}.phone .screen-icon{margin-top:9px}.navlinks{gap:9px}.cards{grid-template-columns:1fr}.release-grid{grid-template-columns:1fr}.release-grid .button{width:100%}}
  </style>
  <script src="/client.js" defer></script>
</head>
<body>
  <header><nav class="wrap" aria-label="Navegação principal">
    <a class="brand" href="/"><span class="brand-mark" aria-hidden="true">🐺</span><span>THE WORKSHOP / MOBILE</span></a>
    <div class="navlinks"><a href="#academy">Academy</a><a href="#instalar">Instalação</a><a href="https://github.com/kingmaker-lab/The-Workshop." rel="noopener noreferrer">GitHub</a></div>
  </nav></header>
  <main>
    <section class="hero wrap" aria-labelledby="titulo">
      <div>
        <div class="eyebrow">Build. Break. Understand. Rebuild.</div>
        <h1 id="titulo">Conhecimento<br>no <span>seu bolso.</span></h1>
        <p class="lead">A divisão mobile da The Workshop está nascendo. Jogos, programação e desafios feitos para quem quer aprender de verdade, sem anúncios, sem cadastro e sem pagar para estudar.</p>
        <div class="pills"><span class="pill">Android</span><span class="pill">Gratuito</span><span class="pill">Offline first</span><span class="pill">Código aberto em avaliação</span></div>
      </div>
      <div class="phone" aria-label="Representação ilustrativa do aplicativo Wolfpack Academy">
        <span class="screen-icon" aria-hidden="true">🐺</span><small>WOLFPACK ACADEMY</small><h3>Sua jornada começa aqui.</h3>
        <div class="screen-card">Lógica de programação<div class="screen-meter"></div></div>
        <div class="screen-card">Caça aos bugs</div>
      </div>
    </section>
    <section class="wrap" id="academy">
      <div class="panel">
        <span class="tag">01 / Primeiro aplicativo</span>
        <div class="release-grid">
          <div>
            <h2>Wolfpack Academy <span style="color:#60d5ef">Beta 0.2</span></h2>
            <p class="description">25 desafios de lógica, depuração e fundamentos web; cinco níveis, conquistas e progresso salvo no aparelho. Conteúdos disponíveis offline.</p>
            <p id="release-status" role="status" aria-live="polite" class="faint">Consultando a versão assinada no GitHub Releases...</p>
          </div>
          <a class="button" id="download" href="#instalar" aria-disabled="true" tabindex="-1">APK assinado indisponível</a>
        </div>
        <div class="digest"><strong>SHA-256:</strong> <span id="sha256">Aguardando APK assinado e checksum publicado.</span><div id="release-meta" class="faint"></div></div>
        <p class="faint">Apenas releases oficiais assinados serão disponibilizados aqui. Nunca instale versões recebidas de fontes desconhecidas.</p>
      </div>
    </section>
    <section class="wrap">
      <h2>Aprender é experimentar.</h2>
      <div class="cards">
        <article class="card"><div class="icon" aria-hidden="true">🧩</div><strong>25 desafios</strong><p>Problemas progressivos e explicações que ensinam o raciocínio, não só a resposta.</p></article>
        <article class="card"><div class="icon" aria-hidden="true">🏆</div><strong>XP e conquistas</strong><p>Cinco níveis. Cada missão só vale pontos uma vez. Seu progresso continua no dispositivo.</p></article>
        <article class="card"><div class="icon" aria-hidden="true">📴</div><strong>Funciona offline</strong><p>Sem precisar enviar seu progresso para servidores ou criar conta para estudar.</p></article>
      </div>
    </section>
    <section class="wrap" id="instalar">
      <h2>Instalação e verificação</h2>
      <ol class="steps">
        <li>Baixe somente pelo botão oficial acima, quando o APK assinado estiver disponível.</li>
        <li>No computador, compare o SHA-256 informado nesta página com <code>sha256sum nome-do-arquivo.apk</code>.</li>
        <li>No Android, abra o arquivo e siga as instruções do sistema para instalar. No Brasil, instalações fora da Play Store podem exigir etapas adicionais de verificação.</li>
        <li>Para atualizar mantendo o progresso, use a mesma assinatura e o mesmo identificador de pacote. Não desinstale a versão anterior sem backup.</li>
      </ol>
      <p class="faint">Testes limitados via Android Developer Console e análise de publicação F-Droid estão em preparação. A Google Play Store continua sendo uma meta futura.</p>
    </section>
  </main>
  <footer class="footer"><div class="wrap">© The Workshop · Mobile Division · <a href="https://github.com/kingmaker-lab/The-Workshop." rel="noopener noreferrer">Código e projetos</a></div></footer>
</body>
</html>`;
const CLIENT = String.raw`(() => {
  const status = document.getElementById("release-status");
  const btn = document.getElementById("download");
  const hash = document.getElementById("sha256");
  const meta = document.getElementById("release-meta");
  fetch("/api/release", { headers: { Accept: "application/json" } })
    .then(r => { if (!r.ok) throw new Error("status"); return r.json(); })
    .then(data => {
      if (!data.available) {
        status.textContent = "Release assinado ainda em preparação. A versão debug não será publicada aqui.";
        return;
      }
      status.textContent = "Disponível: " + data.version + " • arquivo APK de release assinado";
      hash.textContent = data.sha256;
      meta.textContent = data.filename + " • " + (data.size / 1048576).toFixed(1) + " MiB";
      btn.href = data.url;
      btn.textContent = "Baixar Android APK";
      btn.removeAttribute("aria-disabled");
      btn.removeAttribute("tabindex");
      btn.rel = "noopener noreferrer";
    })
    .catch(() => {
      status.textContent = "Não foi possível consultar o GitHub agora. Tente novamente mais tarde.";
    });
})();`;

const respond = (body, status, type, more = {}) =>
  new Response(body, {
    status, headers: { ...HEADERS, ...more, "Content-Type": type }
  });

async function releaseResponse() {
  try {
    const r = await fetch(RELEASES_API, {
      headers: { "Accept": "application/vnd.github+json", "User-Agent": "TheWorkshopMobilePortal/0.1" },
      cf: { cacheEverything: true, cacheTtl: 300 }
    });
    if (!r.ok) throw new Error("release request failed");
    const list = await r.json();
    if (!Array.isArray(list)) throw new Error("release format");
    const release = list.find(item => !item.draft && !item.prerelease &&
      /^wolfpack-academy-vd+.d+.d+$/.test(item.tag_name || ""));
    if (!release) return {available:false};
    const name = release.tag_name + ".apk";
    const asset = (release.assets || []).find(item => item.name === name);
    const digest = asset && /^sha256:[0-9a-f]{64}$/i.test(asset.digest || "") ? asset.digest.slice(7).toLowerCase() : null;
    const validUrl = asset && asset.browser_download_url ===
      "https://github.com/" + REPO + "/releases/download/" + release.tag_name + "/" + name;
    if (!asset || !digest || !validUrl) return {available:false};
    return {available:true,version:release.tag_name,filename:name,sha256:digest,url:asset.browser_download_url,size:asset.size};
  } catch (_) {
    return {available:false};
  }
}

export default {
  async fetch(request) {
    const u = new URL(request.url);
    if (request.method !== "GET" && request.method !== "HEAD") {
      return respond("Method not allowed", 405, "text/plain; charset=utf-8", {"Allow":"GET, HEAD"});
    }
    if (u.pathname === "/" || u.pathname === "/mobile" || u.pathname === "/mobile/") {
      return respond(request.method === "HEAD" ? null : PAGE, 200, "text/html; charset=utf-8", {
        "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'; upgrade-insecure-requests",
        "Cache-Control": "public, max-age=300"
      });
    }
    if (u.pathname === "/client.js") {
      return respond(request.method === "HEAD" ? null : CLIENT, 200, "application/javascript; charset=utf-8", {
        "Cache-Control":"public, max-age=300"
      });
    }
    if (u.pathname === "/api/release") {
      return respond(request.method === "HEAD" ? null : JSON.stringify(await releaseResponse()), 200, "application/json; charset=utf-8", {
        "Cache-Control":"public, max-age=300"
      });
    }
    if (u.pathname === "/health") {
      return respond(JSON.stringify({ok:true,site:"workshop-mobile"}),200,"application/json; charset=utf-8");
    }
    return respond("Página não encontrada",404,"text/plain; charset=utf-8");
  }
};
