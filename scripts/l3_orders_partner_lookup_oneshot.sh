#!/usr/bin/env bash
set -euo pipefail

# L-3 one-shot: lookup dedicado de orders por parceiro/ref
# Cobre:
#   1) cenário de sucesso (partner_id + partner_order_ref)
#   2) cenário de erro controlado (sem match / parceiro inválido)
#
# Uso mínimo:
#   OPS_TOKEN=... ./scripts/l3_orders_partner_lookup_oneshot.sh
#
# Variáveis opcionais:
#   BASE_URL (default: http://localhost:8000)
#   PARTNER_ID_REAL (default: partner_demo_001)
#   PARTNER_ORDER_REF_REAL (default: PO-7788)
#   LIMIT (default: 20)
#   OFFSET (default: 0)
#   INVALID_PARTNER_ID (default: partner_invalido_404)

BASE_URL="${BASE_URL:-http://localhost:8000}"
OPS_TOKEN="${OPS_TOKEN:-}"
PARTNER_ID_REAL="${PARTNER_ID_REAL:-partner_demo_001}"
PARTNER_ORDER_REF_REAL="${PARTNER_ORDER_REF_REAL:-PO-7788}"
LIMIT="${LIMIT:-20}"
OFFSET="${OFFSET:-0}"
INVALID_PARTNER_ID="${INVALID_PARTNER_ID:-partner_invalido_404}"

if [[ -z "${OPS_TOKEN}" ]]; then
  echo "ERRO: defina OPS_TOKEN"
  exit 1
fi

AUTH_HEADER="Authorization: Bearer ${OPS_TOKEN}"
AC_HEADER="Accept: application/json"

echo "== L-3 partner-lookup one-shot =="
echo "BASE_URL=${BASE_URL}"
echo "PARTNER_ID_REAL=${PARTNER_ID_REAL}"
echo "PARTNER_ORDER_REF_REAL=${PARTNER_ORDER_REF_REAL}"
echo

echo "1) SUCESSO - GET /orders/partner-lookup (partner + ref)"
success_url="${BASE_URL}/orders/partner-lookup?partner_id=${PARTNER_ID_REAL}&partner_order_ref=${PARTNER_ORDER_REF_REAL}&limit=${LIMIT}&offset=${OFFSET}"
success_body="$(
  curl -sS -X GET "${success_url}" \
    -H "${AUTH_HEADER}" \
    -H "${AC_HEADER}" \
    -w "\nHTTP_STATUS:%{http_code}"
)"
success_status="$(printf "%s" "${success_body}" | sed -n 's/.*HTTP_STATUS:\([0-9][0-9][0-9]\)$/\1/p')"
success_json="$(printf "%s" "${success_body}" | sed 's/\nHTTP_STATUS:[0-9][0-9][0-9]$//')"
echo "HTTP ${success_status}"
echo "${success_json}"
echo

echo "2) ERRO CONTROLADO - GET /orders/partner-lookup (partner inválido/sem match)"
error_url="${BASE_URL}/orders/partner-lookup?partner_id=${INVALID_PARTNER_ID}&partner_order_ref=SEM_MATCH_${RANDOM}&limit=5&offset=0"
error_body="$(
  curl -sS -X GET "${error_url}" \
    -H "${AUTH_HEADER}" \
    -H "${AC_HEADER}" \
    -w "\nHTTP_STATUS:%{http_code}"
)"
error_status="$(printf "%s" "${error_body}" | sed -n 's/.*HTTP_STATUS:\([0-9][0-9][0-9]\)$/\1/p')"
error_json="$(printf "%s" "${error_body}" | sed 's/\nHTTP_STATUS:[0-9][0-9][0-9]$//')"
echo "HTTP ${error_status}"
echo "${error_json}"
echo

echo "== DONE =="
echo "Cole no doc: sucesso HTTP ${success_status}; erro-controlado HTTP ${error_status}."
