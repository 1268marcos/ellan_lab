#!/usr/bin/env bash
set -euo pipefail

# L-2 D2 one-shot: fila + quick actions de ops/logistics/returns
# Uso mínimo:
#   OPS_TOKEN=... ./scripts/l2_d2_ops_returns_queue_oneshot.sh
#
# Uso com criação opcional de request (quando não houver RETURN_ID_REAL pronto):
#   OPS_TOKEN=... DELIVERY_ID_REAL=... ./scripts/l2_d2_ops_returns_queue_oneshot.sh
#
# Variáveis opcionais:
#   BASE_URL (default: http://localhost:8003)
#   RETURN_ID_REAL (se já existir um return_request)
#   DELIVERY_ID_REAL (usado para criar request quando RETURN_ID_REAL não for informado)
#   REQUESTER_ID_REAL (default: usr_ops_001)
#   RETURN_REASON_CODE (default: DAMAGED_ITEM)

BASE_URL="${BASE_URL:-http://localhost:8003}"
OPS_TOKEN="${OPS_TOKEN:-}"
RETURN_ID_REAL="${RETURN_ID_REAL:-}"
DELIVERY_ID_REAL="${DELIVERY_ID_REAL:-}"
REQUESTER_ID_REAL="${REQUESTER_ID_REAL:-usr_ops_001}"
RETURN_REASON_CODE="${RETURN_REASON_CODE:-DAMAGED_ITEM}"

if [[ -z "${OPS_TOKEN}" ]]; then
  echo "ERRO: defina OPS_TOKEN"
  exit 1
fi

AUTH_HEADER="Authorization: Bearer ${OPS_TOKEN}"
CT_HEADER="Content-Type: application/json"
AC_HEADER="Accept: application/json"

echo "== L-2 D2 one-shot (queue + quick actions) =="
echo "BASE_URL=${BASE_URL}"
echo

echo "1) LIST queue (REQUESTED)"
queue_resp="$(
  curl -sS -X GET "${BASE_URL}/logistics/return-requests?status=REQUESTED&limit=20&offset=0" \
    -H "${AUTH_HEADER}" \
    -H "${AC_HEADER}"
)"
echo "${queue_resp}"
echo

if [[ -z "${RETURN_ID_REAL}" ]]; then
  RETURN_ID_REAL="$(
    RESPONSE_JSON="${queue_resp}" python - <<'PY'
import json, os
raw = os.environ.get("RESPONSE_JSON", "{}")
try:
    data = json.loads(raw)
except Exception:
    data = {}
items = data.get("items") or []
first = items[0] if items else {}
print(first.get("id", ""))
PY
)"
fi

if [[ -z "${RETURN_ID_REAL}" && -n "${DELIVERY_ID_REAL}" ]]; then
  echo "2) UPSERT reason + CREATE return request (fallback para obter RETURN_ID_REAL)"
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
    }" >/dev/null

  create_resp="$(
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
  echo "${create_resp}"
  echo
  RETURN_ID_REAL="$(
    RESPONSE_JSON="${create_resp}" python - <<'PY'
import json, os
raw = os.environ.get("RESPONSE_JSON", "{}")
try:
    data = json.loads(raw)
except Exception:
    data = {}
print(data.get("id", ""))
PY
)"
fi

if [[ -z "${RETURN_ID_REAL}" ]]; then
  echo "ERRO: não foi possível obter RETURN_ID_REAL."
  echo "Dica: informe RETURN_ID_REAL diretamente ou DELIVERY_ID_REAL para criação fallback."
  exit 1
fi
echo "RETURN_ID_REAL=${RETURN_ID_REAL}"
echo

echo "3) QUICK ACTION - GET detail"
detail_resp="$(
  curl -sS -X GET "${BASE_URL}/logistics/return-requests/${RETURN_ID_REAL}" \
    -H "${AUTH_HEADER}" \
    -H "${AC_HEADER}"
)"
echo "${detail_resp}"
echo

echo "4) QUICK ACTION - PATCH status -> APPROVED"
patch_resp="$(
  curl -sS -X PATCH "${BASE_URL}/logistics/return-requests/${RETURN_ID_REAL}/status" \
    -H "${AUTH_HEADER}" \
    -H "${CT_HEADER}" \
    -d '{"status":"APPROVED"}'
)"
echo "${patch_resp}"
echo

echo "5) QUICK ACTION - POST labels"
label_resp="$(
  curl -sS -X POST "${BASE_URL}/logistics/return-requests/${RETURN_ID_REAL}/labels" \
    -H "${AUTH_HEADER}" \
    -H "${AC_HEADER}"
)"
echo "${label_resp}"
echo

echo "6) QUICK ACTION - GET SLA breaches by return_request_id"
sla_resp="$(
  curl -sS -X GET "${BASE_URL}/logistics/sla-breaches?return_request_id=${RETURN_ID_REAL}&limit=30&offset=0" \
    -H "${AUTH_HEADER}" \
    -H "${AC_HEADER}"
)"
echo "${sla_resp}"
echo

echo "7) ERROR CONTROLADO - GET detail inexistente (espera-se 404)"
missing_id="rr_missing_$(date +%s)"
error_resp="$(
  curl -sS -X GET "${BASE_URL}/logistics/return-requests/${missing_id}" \
    -H "${AUTH_HEADER}" \
    -H "${AC_HEADER}"
)"
echo "${error_resp}"
echo

echo "== DONE =="
echo "Use RETURN_ID_REAL=${RETURN_ID_REAL} no anexo de evidência."
