
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { ELLAN_FRONTEND_CSP, ELLAN_FRONTEND_CSP_META } from "./ellan-frontend-csp.mjs";

/**
 * CSP (fonte: ./ellan-frontend-csp.mjs):
 * - Dev (vite serve): meta no HTML com placeholder → substituída pela política + unsafe-inline em script-src (HMR).
 * - Build: meta removida do dist — produção: header no gateway (02_docker/nginx/csp-frontend.example.conf).
 * - vite preview: header Content-Security-Policy (mesmo valor), pois o dist não tem meta.
 */
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

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), ellanCspIndexHtml()],
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
    },
  },
});

