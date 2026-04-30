/**
 * Fonte única do valor de Content-Security-Policy para o frontend ELLAN Lab.
 * Usado em: meta (dev, via vite.config.js), header vite preview, documentação do gateway.
 * Não incluir quebras de linha (Nginx add_header / header HTTP).
 */
/** CSP completa (header HTTP / vite preview / gateway). Inclui frame-ancestors — nao usar em meta tag (browser ignora). */
export const ELLAN_FRONTEND_CSP =
  "default-src 'self'; base-uri 'self'; form-action 'self'; object-src 'none'; frame-ancestors 'none'; frame-src 'none'; img-src 'self' data: https:; font-src 'self' data: https:; media-src 'self' data: https:; style-src 'self' 'unsafe-inline'; script-src 'self'; worker-src 'self'; manifest-src 'self'; connect-src 'self' http://127.0.0.1:8000 http://127.0.0.1:8003 http://127.0.0.1:8010 http://127.0.0.1:8020 http://127.0.0.1:8200 http://127.0.0.1:8201 http://127.0.0.1:8202 http://localhost:8000 http://localhost:8003 http://localhost:8010 http://localhost:8020 http://localhost:8200 http://localhost:8201 http://localhost:8202 ws://127.0.0.1:5173 ws://127.0.0.1:5174 ws://127.0.0.1:4173 ws://localhost:5173 ws://localhost:5174 ws://localhost:4173 https://api.github.com https://github.com";

/** Igual a completa, sem frame-ancestors — valida em meta http-equiv (dev). Em producao, frame-ancestors no header Nginx. */
export const ELLAN_FRONTEND_CSP_META = ELLAN_FRONTEND_CSP.replace(
  /\s*frame-ancestors\s+[^;]+;\s*/i,
  " "
).replace(/\s{2,}/g, " ").trim();
