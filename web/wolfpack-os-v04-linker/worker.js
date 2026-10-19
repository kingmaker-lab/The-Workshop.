/**
 * WOLFPACK OS v0.4.1 — ARES + CERBERUS card links
 *
 * Keep the deployed v0.4 asset manifest unchanged (Cloudflare keep_assets:true).
 * Rewrites only the public landing page using HTMLRewriter.
 * All games (Ruby Protocol, VULPES-77, RAVEN), JS modules and ZIP downloads
 * remain served by the existing Cloudflare Static Assets binding, unchanged.
 *
 * The card indexes are checked against a v0.4.0 browser-exported HTML snapshot.
 */
const DESTINATIONS = Object.freeze({
  ares: "https://workshop-labs.pages.dev/projects/ares/",
  cerberus: "https://cerberus.wolfpackworkshop.workers.dev/",
});

function linkCard(href, label) {
  return {
    element(el) {
      el.tagName = "a";
      el.setAttribute("href", href);
      el.setAttribute("aria-label", label);
      el.setAttribute("rel", "noopener noreferrer");
      el.setAttribute("referrerpolicy", "no-referrer");
    },
  };
}
function replaceText(value, extraClass) {
  return {
    element(el) {
      el.setInnerContent(value);
      if (extraClass) el.setAttribute("class", extraClass);
    },
  };
}

export const cardRoutes = DESTINATIONS;

export default {
  async fetch(request, env) {
    // This handler is intended to run first on / and /index.html only.
    // Even if the rule is inadvertently broadened, preserve every other asset.
    const path = new URL(request.url).pathname;
    const original = await env.ASSETS.fetch(request);
    if (!["/", "/index.html"].includes(path)
      || request.method !== "GET"
      || original.status !== 200
      || !original.headers.get("content-type")?.toLowerCase().includes("text/html")) {
      return original;
    }

    const result = new HTMLRewriter()
      .on(".app-grid > article.app-card:nth-child(3)", linkCard(
        DESTINATIONS.ares,
        "Abrir o laboratório ARES Protocol",
      ))
      .on(".app-grid > article.app-card:nth-child(6)", linkCard(
        DESTINATIONS.cerberus,
        "Abrir o laboratório CERBERUS de Arquitetura de Software",
      ))
      .on(".app-grid > article.app-card:nth-child(3) .status",
        replaceText("● DISPONÍVEL", "status status-live"))
      .on(".app-grid > article.app-card:nth-child(6) .status",
        replaceText("● DISPONÍVEL", "status status-live"))
      .on(".app-grid > article.app-card:nth-child(3) .app-card-bottom .app-muted",
        replaceText("ACESSAR ARES →", "app-link-label"))
      .on(".app-grid > article.app-card:nth-child(6) .app-card-body small",
        replaceText("ENGENHARIA / ARQUITETURA DE SOFTWARE"))
      .on(".app-grid > article.app-card:nth-child(6) .app-card-body p",
        replaceText("Explore decisões arquiteturais, padrões, qualidade e sistemas distribuídos por meio de experimentos."))
      .on(".app-grid > article.app-card:nth-child(6) .app-card-bottom span:first-child",
        replaceText("SOFTWARE ARCHITECTURE LAB"))
      .on(".app-grid > article.app-card:nth-child(6) .app-card-bottom .app-muted",
        replaceText("ABRIR CERBERUS →", "app-link-label"))
      .on("style#wolfpack-critical-css", {
        element(el) {
          el.append(".app-card[href]:focus-visible{outline:2px solid var(--lime);outline-offset:3px}.app-card[href] .app-link-label{color:var(--lime);font-weight:700;white-space:nowrap}.app-card[href]:hover .app-link-label{text-decoration:underline;text-underline-offset:3px}");
        },
      })
      .transform(original);

    // Avoid serving the static asset's stale entity metadata with a modified body.
    const headers = new Headers(result.headers);
    headers.delete("content-length");
    headers.delete("etag");
    headers.delete("last-modified");
    headers.set("cache-control", "public, max-age=60, s-maxage=60");
    return new Response(result.body, {
      status: result.status,
      statusText: result.statusText,
      headers,
    });
  },
};
