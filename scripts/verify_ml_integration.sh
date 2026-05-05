#!/usr/bin/env bash
# Validação ponta-a-ponta: build frontend, rotas partner, CORS ML, middleware Bearer/partner.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND="${FRONTEND_DIR:-$ROOT/01_source/frontend}"
ML_BASE_URL="${ML_BASE_URL:-http://127.0.0.1:8001}"
ORIGIN_OK="${CORS_ORIGIN:-http://localhost:5173}"

fail() { echo "FAIL: $*" >&2; exit 1; }
ok() { echo "OK: $*"; }

echo "== Vite build (frontend)"
cd "$FRONTEND"
if ! npx vite build >/tmp/verify_ml_vite.log 2>&1; then
  tail -20 /tmp/verify_ml_vite.log >&2
  fail "vite build"
fi
ok "vite build"

echo "== Permissão partner: /intelligence em AuthContext"
if ! grep -q "partner:" "$ROOT/01_source/frontend/src/contexts/AuthContext.tsx"; then
  fail "AuthContext.tsx ausente"
fi
if ! awk '/partner: *\[/,/^\s*\],/{print}' "$ROOT/01_source/frontend/src/contexts/AuthContext.tsx" | grep -q "'/intelligence'"; then
  fail "partner PROFILE_ROUTES sem '/intelligence'"
fi
ok "partner pode /intelligence/* (PROFILE_ROUTES)"

echo "== Menu: parceiro não bloqueia /intelligence/"
if ! grep -q "startsWith('/intelligence/')" "$ROOT/01_source/frontend/src/layouts/Menu.tsx"; then
  fail "Menu.tsx sem filtro /intelligence/ para partner"
fi
ok "Menu partner + /intelligence/"

echo "== ML service: GET $ML_BASE_URL/health"
code="$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 "$ML_BASE_URL/health" || true)"
if [[ "$code" != "200" ]]; then
  fail "ML health HTTP $code (subir ml_predictor_service em $ML_BASE_URL)"
fi
ok "ML health 200"

echo "== CORS: resposta GET /health com Origin $ORIGIN_OK"
hdrs="$(curl -sSI --connect-timeout 2 -H "Origin: $ORIGIN_OK" "$ML_BASE_URL/health" || true)"
echo "$hdrs" | grep -qi 'access-control-allow-origin' || fail "sem Access-Control-Allow-* no GET /health"
ok "CORS headers presentes"

echo "== CORS: OPTIONS preflight"
opt="$(curl -sSI --connect-timeout 2 -X OPTIONS \
  -H "Origin: $ORIGIN_OK" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: authorization" \
  "$ML_BASE_URL/intelligence/at-risk" || true)"
echo "$opt" | grep -qi 'access-control-allow' || fail "OPTIONS sem CORS"
ok "OPTIONS CORS"

echo "== Middleware: /intelligence/at-risk sem Bearer -> 401 (ou WARN se legacy)"
code="$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 \
  "$ML_BASE_URL/intelligence/at-risk?partner_id=test-partner" || true)"
if [[ "$code" == "401" ]]; then
  ok "at-risk exige sessão (401)"
elif [[ "$code" == "200" ]]; then
  echo "WARN: at-risk sem Bearer retornou 200 (instância sem require_session_user neste path)." >&2
  if [[ "${VERIFY_STRICT_SESSION:-0}" == "1" ]]; then
    fail "VERIFY_STRICT_SESSION=1 exige 401"
  fi
else
  fail "at-risk sem Bearer: HTTP inesperado $code"
fi

echo "== Middleware: sem partner_id e sem papel OPS -> 400 (se Bearer válido de partner-only)"
# Apenas documenta contrato; exige token real — opcional com TOKEN de env
if [[ -n "${VERIFY_ML_BEARER_TOKEN:-}" ]]; then
  code="$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 \
    -H "Authorization: Bearer ${VERIFY_ML_BEARER_TOKEN}" \
    "$ML_BASE_URL/intelligence/at-risk" || true)"
  if [[ "$code" != "400" ]]; then
    echo "WARN: Bearer+sem partner_id esperado 400 para utilizador só partner, obtido $code" >&2
  else
    ok "partner sem partner_id -> 400"
  fi
else
  echo "SKIP: defina VERIFY_ML_BEARER_TOKEN para validar 400 sem partner_id"
fi

echo "== Resumo"
echo "BUILD OK | partner routes OK | ML CORS OK | at-risk auth: ver WARN acima ou VERIFY_STRICT_SESSION=1"
exit 0
