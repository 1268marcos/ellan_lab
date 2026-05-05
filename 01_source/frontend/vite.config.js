import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { ELLAN_FRONTEND_CSP, ELLAN_FRONTEND_CSP_META } from "./ellan-frontend-csp.mjs";

function ellanCspIndexHtml() {
  const cspMetaRe = /\s*<meta[\s\S]*?http-equiv\s*=\s*["']Content-Security-Policy["'][\s\S]*?\/>/gi;
  return {
    name: "ellan-csp-index-html",
    transformIndexHtml(html, ctx) {
      if (ctx.server) {
        let out = html.replaceAll("ELLAN_FRONTEND_CSP_PLACEHOLDER", ELLAN_FRONTEND_CSP_META);
        if (!/http-equiv\s*=\s*["']Content-Security-Policy["']/i.test(out)) {
          out = out.replace(
            "<head>",
            `<head>\n    <meta http-equiv="Content-Security-Policy" content="${ELLAN_FRONTEND_CSP_META.replaceAll('"', "&quot;")}" />`,
          );
        }
        return out.replace(/script-src 'self';/g, "script-src 'self' 'unsafe-inline';");
      }
      return html.replace(cspMetaRe, "\n");
    },
  };
}

export default defineConfig({
  plugins: [
    react(),
    ellanCspIndexHtml(),
    // plugin mkcert REMOVIDO
  ],
  /** Evita postcss-load-config a subir pastas (ex.: outro frontend no monorepo) e falhar ao dar parse JSON. */
  css: {
    postcss: {
      plugins: [],
    },
  },
  preview: {
    headers: {
      "Content-Security-Policy": ELLAN_FRONTEND_CSP,
    },
  },
  test: {
    environment: "happy-dom",
    setupFiles: "./src/test/setupTests.js",
    exclude: ["**/node_modules/**", "**/e2e/**", "**/dist/**"],
    pool: "threads",
  },
  server: {
    https: false,        // ← MUDADO para false
    host: true,
    port: 5173,
    strictPort: true,
    proxy: {
      "/api/sp": {
        target: "http://localhost:8201",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/sp/, ""),
      },
      "/api/pt": {
        target: "http://localhost:8202",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/pt/, ""),
      },
      "/api/gw": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/gw/, ""),
      },
      "/api/op": {
        target: "http://localhost:8003",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/op/, ""),
      },
      "/api/rt": {
        target: "http://localhost:8200",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/rt/, ""),
      },
      "/api/ol": {
        target: "http://localhost:8010",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/ol/, ""),
      },
      "/api/bf": {
        target: "http://localhost:8020",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/bf/, ""),
      },
      "/api/wallet-svc": {
        target: "http://localhost:8004",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/wallet-svc/, "/api"),
      },
    },
  },
});