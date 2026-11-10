const FILES = /*__STATIC_FILES__*/;
const SECURE_HEADERS = Object.freeze({
  "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'none'; base-uri 'none'; object-src 'none'; form-action 'none'; frame-ancestors 'none'; upgrade-insecure-requests",
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
  "Referrer-Policy": "no-referrer",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
  "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
  "Cross-Origin-Opener-Policy": "same-origin",
  "Cross-Origin-Resource-Policy": "same-origin"
});

export default {
  async fetch(request) {
    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response("Method Not Allowed", { status: 405, headers: { ...SECURE_HEADERS, Allow: "GET, HEAD", "Cache-Control": "no-store" } });
    }
    const url = new URL(request.url);
    const previewOnly = url.hostname === "workshop-store-preview.wolfpackworkshop.workers.dev";
    const requestHeaders = previewOnly ? { ...SECURE_HEADERS, "X-Robots-Tag": "noindex, nofollow, noarchive" } : SECURE_HEADERS;
    const knownPath = Object.hasOwn(FILES, url.pathname);
    if (!knownPath) {
      return new Response(request.method === "HEAD" ? null : "Not Found", { status: 404, headers: { ...requestHeaders, "Cache-Control": "no-store", "Content-Type": "text/plain; charset=utf-8" } });
    }
    const file = FILES[url.pathname];
    return new Response(request.method === "HEAD" ? null : file.body, {
      status: 200,
      headers: {
        ...requestHeaders,
        "Content-Type": file.mime,
        "Cache-Control": url.pathname === "/config.js" || url.pathname === "/index.html" || url.pathname === "/" ? "no-store" : "public, max-age=300",
      }
    });
  }
};
