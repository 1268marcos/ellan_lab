#!/usr/bin/env bash
set -euo pipefail

# L-2 D1 one-shot: executa fluxo mínimo para coletar respostas 200
# Uso:
#   OPS_TOKEN=... DELIVERY_ID_REAL=... ./scripts/l2_d1_ops_validation_oneshot.sh
# Variáveis opcionais:
#   BASE_URL (default: http://localhost:8003)
#   REQUESTER_ID_REAL (default: usr_ops_001)
#   RETURN_REASON_CODE (default: DAMAGED_ITEM)

BASE_URL="${BASE_URL:-http://localhost:8003}"
OPS_TOKEN="${OPS_TOKEN:-}"
DELIVERY_ID_REAL="${DELIVERY_ID_REAL:-}"
REQUESTER_ID_REAL="${REQUESTER_ID_REAL:-usr_ops_001}"
RETURN_REASON_CODE="${RETURN_REASON_CODE:-DAMAGED_ITEM}"

if [[ -z "${OPS_TOKEN}" ]]; then
  echo "ERRO: defina OPS_TOKEN"
  exit 1
fi
if [[ -z "${DELIVERY_ID_REAL}" ]]; then
  echo "ERRO: defina DELIVERY_ID_REAL"
  exit 1
fi

AUTH_HEADER="Authorization: Bearer ${OPS_TOKEN}"
CT_HEADER="Content-Type: application/json"
AC_HEADER="Accept: application/json"

echo "== L-2 D1 one-shot =="
echo "BASE_URL=${BASE_URL}"
echo "DELIVERY_ID_REAL=${DELIVERY_ID_REAL}"
echo "RETURN_REASON_CODE=${RETURN_REASON_CODE}"
echo

echo "1) UPSERT return reason"
reason_resp="$(
  curl -sS -X POST "${BASE_URL}/logistics/return-reasons" \
    -H "${AUTH_HEADER}" \
    -H "${CT_HEADER}" \
    -d "{
      \"code\": \"${RETURN_REASON_CODE}\",
      \"label_pt\": \"Produto avariado\",
      \"label_en\": \"Damaged item\",
      \"category\": \"PRODUCT\",
      \"requires_photo\": true,
      \"requires_detail\": true,
      \"is_active\": true
    }"
)"
echo "${reason_resp}"
echo

echo "2) CREATE return request"
request_resp="$(
  curl -sS -X POST "${BASE_URL}/logistics/deliveries/${DELIVERY_ID_REAL}/return-request" \
    -H "${AUTH_HEADER}" \
    -H "${CT_HEADER}" \
    -d "{
      \"requester_type\": \"RECIPIENT\",
      \"requester_id\": \"${REQUESTER_ID_REAL}\",
      \"return_reason_code\": \"${RETURN_REASON_CODE}\",
      \"return_reason_detail\": \"Avaria em embalagem\"
    }"
)"
echo "${request_resp}"
echo

RETURN_ID_REAL="$(
  RESPONSE_JSON="${request_resp}" python - <<'PY'
import json, os
raw = os.environ.get("RESPONSE_JSON", "{}")
try:
    data = json.loads(raw)
except Exception:
    data = {}
print(data.get("id", ""))
PY
)"
if [[ -z "${RETURN_ID_REAL}" ]]; then
  echo "ERRO: nao foi possivel extrair RETURN_ID_REAL da resposta do passo 2."
  exit 1
fi
echo "RETURN_ID_REAL=${RETURN_ID_REAL}"
echo

echo "3) PATCH return request status -> APPROVED"
status_resp="$(
  curl -sS -X PATCH "${BASE_URL}/logistics/return-requests/${RETURN_ID_REAL}/status" \
    -H "${AUTH_HEADER}" \
    -H "${CT_HEADER}" \
    -d '{"status":"APPROVED"}'
)"
echo "${status_resp}"
echo

echo "4) CREATE reverse label"
label_resp="$(
  curl -sS -X POST "${BASE_URL}/logistics/return-requests/${RETURN_ID_REAL}/labels" \
    -H "${AUTH_HEADER}" \
    -H "${AC_HEADER}"
)"
echo "${label_resp}"
echo

echo "5) LIST sla breaches"
breach_resp="$(
  curl -sS -X GET "${BASE_URL}/logistics/sla-breaches?severity=HIGH&resolved=false&limit=50" \
    -H "${AUTH_HEADER}" \
    -H "${AC_HEADER}"
)"
echo "${breach_resp}"
echo

echo "== DONE =="
echo "Guarde RETURN_ID_REAL=${RETURN_ID_REAL} na evidencia."
