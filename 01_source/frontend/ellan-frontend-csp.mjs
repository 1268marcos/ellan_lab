/**
 * Fonte única do valor de Content-Security-Policy para o frontend ELLAN Lab.
 * Usado em: meta (dev, via vite.config.js), header vite preview, documentação do gateway.
 * Não incluir quebras de linha (Nginx add_header / header HTTP).
 *
 * Sprint 3 hardening: baseline ~85% (`ELLAN_FRONTEND_CSP` com `style-src 'unsafe-inline'`).
 * Alvo ~95%: `ELLAN_FRONTEND_CSP_STRICT_STYLE` (sem `unsafe-inline` em estilos) após migração de `style={{}}` / `<style>` inject.
 */
/** CSP completa (header HTTP / vite preview / gateway). Inclui frame-ancestors — nao usar em meta tag (browser ignora). */
export const ELLAN_FRONTEND_CSP =
  "default-src 'self'; base-uri 'self'; form-action 'self'; object-src 'none'; frame-ancestors 'none'; frame-src 'none'; img-src 'self' data: https:; font-src 'self' data: https:; media-src 'self' data: https:; style-src 'self' 'unsafe-inline'; script-src 'self'; script-src-attr 'none'; worker-src 'self' blob:; manifest-src 'self'; navigate-to 'self'; connect-src 'self' http://127.0.0.1:8000 http://127.0.0.1:8003 http://127.0.0.1:8010 http://127.0.0.1:8020 http://127.0.0.1:8200 http://127.0.0.1:8201 http://127.0.0.1:8202 http://localhost:8000 http://localhost:8003 http://localhost:8010 http://localhost:8020 http://localhost:8200 http://localhost:8201 http://localhost:8202 ws://127.0.0.1:5173 ws://127.0.0.1:5174 ws://127.0.0.1:4173 ws://localhost:5173 ws://localhost:5174 ws://localhost:4173 https://api.github.com https://github.com";

/** Mesma política com `style-src 'self'` (sem `'unsafe-inline'`). Staging / gateway após smoke sem estilos inline bloqueados. */
export const ELLAN_FRONTEND_CSP_STRICT_STYLE = ELLAN_FRONTEND_CSP.replace(
  /style-src 'self' 'unsafe-inline'/,
  "style-src 'self'",
);

/**
 * Diretivas ainda a endurecer por ambiente (além de trocar para `ELLAN_FRONTEND_CSP_STRICT_STYLE`).
 * @type {readonly string[]}
 */
export const ELLAN_FRONTEND_CSP_DIRECTIVES_PENDING = [
  "connect-src: remover hosts dev (localhost / ws Vite) em produção; listar APIs + WSS reais",
  "HTTPS: acrescentar upgrade-insecure-requests no header do gateway",
  "report-uri ou report-to: endpoint CSP (opcional)",
];

/** Igual a completa, sem frame-ancestors — valida em meta http-equiv (dev). Em producao, frame-ancestors no header Nginx. */
export const ELLAN_FRONTEND_CSP_META = ELLAN_FRONTEND_CSP.replace(
  /\s*frame-ancestors\s+[^;]+;\s*/i,
  " "
).replace(/\s{2,}/g, " ").trim();
