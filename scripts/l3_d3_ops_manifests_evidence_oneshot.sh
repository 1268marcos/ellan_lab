#!/usr/bin/env bash
set -euo pipefail

# L-3 D3 one-shot: evidência real autenticada de manifests overview + view HTML
#
# Uso mínimo:
#   OPS_TOKEN=... ./scripts/l3_d3_ops_manifests_evidence_oneshot.sh
#
# Variáveis opcionais:
#   BASE_URL (default: http://localhost:8003)
#   FROM_ISO (default: agora -7d)
#   TO_ISO (default: agora)
#   PARTNER_ID (default: vazio)

BASE_URL="${BASE_URL:-http://localhost:8003}"
OPS_TOKEN="${OPS_TOKEN:-}"
PARTNER_ID="${PARTNER_ID:-}"

if [[ -z "${OPS_TOKEN}" ]]; then
  echo "ERRO: defina OPS_TOKEN"
  exit 1
fi

if [[ -z "${FROM_ISO:-}" ]]; then
  FROM_ISO="$(date -u -d '-7 days' '+%Y-%m-%dT%H:%M:%SZ')"
fi
if [[ -z "${TO_ISO:-}" ]]; then
  TO_ISO="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
fi

AUTH_HEADER="Authorization: Bearer ${OPS_TOKEN}"
AC_JSON_HEADER="Accept: application/json"
AC_HTML_HEADER="Accept: text/html"

query="from=${FROM_ISO}&to=${TO_ISO}"
if [[ -n "${PARTNER_ID}" ]]; then
  query="${query}&partner_id=${PARTNER_ID}"
fi

echo "== L-3 D3 one-shot (overview + HTML view) =="
echo "BASE_URL=${BASE_URL}"
echo "FROM_ISO=${FROM_ISO}"
echo "TO_ISO=${TO_ISO}"
echo "PARTNER_ID=${PARTNER_ID:-<global>}"
echo

echo "1) GET /logistics/ops/manifests/overview (autenticado)"
overview_url="${BASE_URL}/logistics/ops/manifests/overview?${query}"
overview_body="$(
  curl -sS -X GET "${overview_url}" \
    -H "${AUTH_HEADER}" \
    -H "${AC_JSON_HEADER}" \
    -w "\nHTTP_STATUS:%{http_code}"
)"
overview_status="$(printf "%s" "${overview_body}" | sed -n 's/.*HTTP_STATUS:\([0-9][0-9][0-9]\)$/\1/p')"
overview_json="$(printf "%s" "${overview_body}" | sed 's/\nHTTP_STATUS:[0-9][0-9][0-9]$//')"
echo "HTTP ${overview_status}"
echo "${overview_json}"
echo

echo "2) GET /logistics/ops/manifests/view (autenticado, HTML)"
view_url="${BASE_URL}/logistics/ops/manifests/view?${query}"
view_headers="$(
  curl -sS -D - -o /tmp/l3_d3_view_body.html -X GET "${view_url}" \
    -H "${AUTH_HEADER}" \
    -H "${AC_HTML_HEADER}"
)"
view_status="$(printf "%s" "${view_headers}" | sed -n 's/^HTTP\/[0-9.]* \([0-9][0-9][0-9]\).*/\1/p' | tail -n 1)"
echo "HTTP ${view_status}"
echo "Saved HTML body to: /tmp/l3_d3_view_body.html"
echo "Response headers:"
echo "${view_headers}" | sed -n '1,20p'
echo

echo "== DONE =="
echo "Anexe no doc: HTTP overview=${overview_status}, HTTP view=${view_status}, e print da view HTML."
