const FILES = /*__STATIC_FILES__*/;
const SECURE_HEADERS = Object.freeze({
  "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'none'; base-uri 'none'; object-src 'none'; form-action 'none'; frame-ancestors 'none'; upgrade-insecure-requests",
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
  "Referrer-Policy": "no-referrer",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
  "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
});

export default {
  async fetch(request) {
    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response("Method Not Allowed", { status: 405, headers: { ...SECURE_HEADERS, Allow: "GET, HEAD", "Cache-Control": "no-store" } });
    }
    const url = new URL(request.url);
    const file = FILES[url.pathname];
    if (!file) {
      return new Response(request.method === "HEAD" ? null : "Not Found", { status: 404, headers: { ...SECURE_HEADERS, "Cache-Control": "no-store", "Content-Type": "text/plain; charset=utf-8" } });
    }
    return new Response(request.method === "HEAD" ? null : file.body, {
      status: 200,
      headers: {
        ...SECURE_HEADERS,
        "Content-Type": file.mime,
        "Cache-Control": url.pathname === "/config.js" || url.pathname === "/index.html" || url.pathname === "/" ? "no-store" : "public, max-age=300",
      }
    });
  }
};
