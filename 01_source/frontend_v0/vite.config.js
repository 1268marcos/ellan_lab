
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

function redirectRootToV0() {
  const handle = (req, res, next) => {
    if (req.url === "/" || req.url === "/index.html") {
      res.statusCode = 302;
      res.setHeader("Location", "/v0/");
      res.end();
      return;
    }
    next();
  };

  return {
    name: "redirect-root-to-v0",
    configureServer(server) {
      server.middlewares.use(handle);
    },
    configurePreviewServer(server) {
      server.middlewares.use(handle);
    },
  };
}

export default defineConfig({
  plugins: [
    redirectRootToV0(),
    react(),
    ellanCspIndexHtml(),
    // plugin mkcert REMOVIDO
  ],
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
    port: 5174,
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
      "/api/ml": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/ml/, ""),
      },
      "/api/lc": {
        target: "http://localhost:8015",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/lc/, "/api"),
      },
      "/api/pa": {
        target: "http://localhost:8016",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/pa/, "/api"),
      },
      "/api/pga": {
        target: "http://localhost:8017",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/pga/, "/api"),
      },
      "/api/opa": {
        target: "http://localhost:8018",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/opa/, "/api"),
      },
      "/api/mka": {
        target: "http://localhost:8019",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/mka/, "/api"),
      },
      "/api/mla": {
        target: "http://localhost:8021",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/mla/, "/api"),
      },
    },
  },
});
