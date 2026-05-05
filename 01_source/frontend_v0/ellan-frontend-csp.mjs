const CONNECT_SRC = [
  "'self'",
  "http://127.0.0.1:8000",
  "http://127.0.0.1:8003",
  "http://127.0.0.1:8010",
  "http://127.0.0.1:8020",
  "http://127.0.0.1:8200",
  "http://127.0.0.1:8201",
  "http://127.0.0.1:8202",
  "http://127.0.0.1:8047",
  "http://localhost:8000",
  "http://localhost:8003",
  "http://localhost:8010",
  "http://localhost:8020",
  "http://localhost:8200",
  "http://localhost:8201",
  "http://localhost:8202",
  "http://localhost:8047",
  "ws://127.0.0.1:5173",
  "ws://127.0.0.1:5174",
  "ws://127.0.0.1:4173",
  "ws://localhost:5173",
  "ws://localhost:5174",
  "ws://localhost:4173",
  "https://api.github.com",
  "https://github.com",
].join(" ");

const BASE_DIRECTIVES = [
  "default-src 'self'",
  "base-uri 'self'",
  "form-action 'self'",
  "object-src 'none'",
  "frame-ancestors 'none'",
  "frame-src 'none'",
  "img-src 'self' data: https:",
  "font-src 'self' data: https:",
  "media-src 'self' data: https:",
  "script-src 'self'",
  "script-src-attr 'none'",
  "worker-src 'self' blob:",
  "manifest-src 'self'",
  `connect-src ${CONNECT_SRC}`,
];

export const ELLAN_FRONTEND_CSP = [...BASE_DIRECTIVES, "style-src 'self' 'unsafe-inline'"].join("; ") + ";";
export const ELLAN_FRONTEND_CSP_META = ELLAN_FRONTEND_CSP;
export const ELLAN_FRONTEND_CSP_STRICT_STYLE = [...BASE_DIRECTIVES, "style-src 'self'"].join("; ") + ";";
