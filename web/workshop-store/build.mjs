import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
const root = dirname(fileURLToPath(import.meta.url));
const files = {
  "/": ["index.html", "text/html; charset=utf-8"],
  "/index.html": ["index.html", "text/html; charset=utf-8"],
  "/styles.css": ["styles.css", "text/css; charset=utf-8"],
  "/app.js": ["app.js", "text/javascript; charset=utf-8"],
  "/catalog.mjs": ["catalog.mjs", "text/javascript; charset=utf-8"],
  "/whatsapp.mjs": ["whatsapp.mjs", "text/javascript; charset=utf-8"],
  "/config.js": ["config.js", "text/javascript; charset=utf-8"],
  "/privacidade": ["privacidade.html", "text/html; charset=utf-8"],
  "/privacidade.html": ["privacidade.html", "text/html; charset=utf-8"]
};
const contents = Object.fromEntries(Object.entries(files).map(([url, [filename, mime]]) => [url, { body: readFileSync(join(root, filename), "utf8"), mime }]));
const tmpl = readFileSync(join(root, "worker.template.mjs"), "utf8");
if (!tmpl.includes("/*__STATIC_FILES__*/")) throw new Error("Missing worker source marker");
const bundled = tmpl.replace("/*__STATIC_FILES__*/", JSON.stringify(contents));
mkdirSync(join(root, "dist"), { recursive: true });
writeFileSync(join(root, "dist", "worker.mjs"), bundled);
console.log("Workshop Store Worker build OK:", Object.keys(contents).length, "routes");
