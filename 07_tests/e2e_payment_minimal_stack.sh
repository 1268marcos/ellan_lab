#!/usr/bin/env bash
# E2E stack mínima: runtime allocate → seed Postgres → (P1) gateway payment/create → pickup payment-confirm.
# P0-only: export E2E_SKIP_GATEWAY=1 para omitir payment_gateway (regressão rápida).
#
# Pré-requisitos:
#   - Stack mínima no ar (ex.: deploy/compose-minimal-stack.sh) com portas mapeadas no host.
#   - Ficheiro de env com ORDER_INTERNAL_TOKEN (ex.: 02_docker/.env ou 02_docker/env.e2e-minimal).
#   - psql, curl e python3 instalados.
#
# Variáveis opcionais:
#   E2E_SKIP_GATEWAY  — "1" omite health + POST /gateway/payment/create (default 0 = P1 ativo)
#   GATEWAY_BASE      — default http://127.0.0.1:8000
#   E2E_ENV_FILE     — caminho para env com ORDER_INTERNAL_TOKEN (default: 02_docker/env.e2e-minimal)
#   E2E_RUN_ID       — sufixo único (default: timestamp)
#   E2E_LOCKER_ID    — default SP-CARAPICUIBA-JDMARILU-LK-002
#   E2E_SLOT         — slot explícito (se vazio, percorre slots válidos do runtime: GET /locker/slots)
#   E2E_REGION       — SP ou PT (default SP)
#   E2E_CURRENCY     — ex. BRL, EUR (default BRL)
#   E2E_PROVIDER     — método no payment-confirm pickup (ex. PIX, CARTAO; default PIX)
#   E2E_USER_ID / E2E_USER_EMAIL — ver bloco de resolução de user_id no seed
#   RUNTIME_BASE, PICKUP_BASE, PG*

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -z "${E2E_ENV_FILE:-}" ]]; then
  if [[ -f "$ROOT_DIR/02_docker/.env" ]]; then
    E2E_ENV_FILE="$ROOT_DIR/02_docker/.env"
  else
    E2E_ENV_FILE="$ROOT_DIR/02_docker/env.e2e-minimal"
  fi
fi
RUNTIME_BASE="${RUNTIME_BASE:-http://127.0.0.1:8200}"
PICKUP_BASE="${PICKUP_BASE:-http://127.0.0.1:8003}"
GATEWAY_BASE="${GATEWAY_BASE:-http://127.0.0.1:8000}"
E2E_SKIP_GATEWAY="${E2E_SKIP_GATEWAY:-0}"
PGHOST="${PGHOST:-127.0.0.1}"
PGPORT="${PGPORT:-5435}"
PGUSER="${PGUSER:-admin}"
PGPASSWORD="${PGPASSWORD:-admin123}"
PGDATABASE="${PGDATABASE:-locker_central}"
E2E_RUN_ID="${E2E_RUN_ID:-$(date +%s)}"
LOCKER_ID="${E2E_LOCKER_ID:-SP-CARAPICUIBA-JDMARILU-LK-002}"
SKU_ID="${E2E_SKU_ID:-cookie_especial}"
E2E_REGION="${E2E_REGION:-SP}"
E2E_CURRENCY="${E2E_CURRENCY:-BRL}"
E2E_PROVIDER="${E2E_PROVIDER:-PIX}"
E2E_AMOUNT_CENTS="${E2E_AMOUNT_CENTS:-1000}"

ORDER_ID="e2e-order-p0-${E2E_RUN_ID}"
ALLOC_ID="al_e2e_p0_${E2E_RUN_ID}"

die() { echo "ERRO: $*" >&2; exit 1; }

sql_string_literal() { printf '%s' "$1" | sed "s/'/''/g"; }

lookup_user_id_by_email() {
  local em="$1"
  [[ -n "$em" ]] || { echo ""; return 0; }
  local em_esc
  em_esc="$(sql_string_literal "$em")"
  psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -v ON_ERROR_STOP=1 -t -A -c \
    "SELECT id FROM users WHERE lower(trim(email)) = lower(trim('${em_esc}')) AND is_active = true AND deleted_at IS NULL LIMIT 1;" \
    | tr -d '[:space:]'
}

http_allocate() {
  local slot="$1"
  local alloc_aid="$2"
  curl -sS -o /tmp/e2e_alloc_body.json -w "%{http_code}" -X POST "${RUNTIME_BASE}/locker/allocate" \
    -H "Content-Type: application/json" \
    -H "X-Locker-Id: ${LOCKER_ID}" \
    -d "{\"slot\":${slot},\"allocation_id\":\"${alloc_aid}\",\"ttl_seconds\":900,\"request_id\":\"e2e-req-${E2E_RUN_ID}\"}"
}

release_allocation() {
  local alloc_aid="$1"
  curl -sS -o /dev/null -X POST "${RUNTIME_BASE}/locker/allocations/${alloc_aid}/release" \
    -H "Content-Type: application/json" \
    -H "X-Locker-Id: ${LOCKER_ID}" \
    -d '{}' || true
}

list_runtime_slot_ids() {
  curl -sfS "${RUNTIME_BASE}/locker/slots" -H "X-Locker-Id: ${LOCKER_ID}" | python3 -c '
import json, sys
data = json.load(sys.stdin)
if not isinstance(data, list) or not data:
    print("empty slots list", file=sys.stderr)
    sys.exit(1)
print(" ".join(str(int(x["slot"])) for x in sorted(data, key=lambda z: int(z["slot"]))))
' || die "Falha ao obter slots do runtime (GET /locker/slots, X-Locker-Id=${LOCKER_ID}). Locker registado?"
}

scan_free_slot() {
  local s probe code
  local slots
  slots="$(list_runtime_slot_ids)"
  [[ -n "${slots// }" ]] || die "Lista de slots vazia para ${LOCKER_ID}"
  for s in ${slots}; do
    probe="al_e2e_probe_${E2E_RUN_ID}_${s}"
    code="$(http_allocate "$s" "$probe")"
    if [[ "$code" == "200" ]]; then
      release_allocation "$probe"
      echo "$s"
      return
    fi
  done
  die "Nenhum slot livre no runtime para ${LOCKER_ID} (percorridos: ${slots})."
}

[[ -f "$E2E_ENV_FILE" ]] || die "Ficheiro de env não encontrado: $E2E_ENV_FILE"

# shellcheck disable=SC2046
INTERNAL_TOKEN="$(grep -E '^ORDER_INTERNAL_TOKEN=' "$E2E_ENV_FILE" | head -1 | cut -d= -f2- | tr -d '\r')"
[[ -n "${INTERNAL_TOKEN}" ]] || die "ORDER_INTERNAL_TOKEN vazio em $E2E_ENV_FILE"

export PGPASSWORD

echo "[1/8] Health runtime"
curl -sfS "${RUNTIME_BASE}/health" >/dev/null || die "Runtime indisponível em ${RUNTIME_BASE}/health"

echo "[2/8] Aguardar pickup /internal/health (até ~120s)"
ok=0
for i in $(seq 1 60); do
  if curl -sfS "${PICKUP_BASE}/internal/health" -H "X-Internal-Token: ${INTERNAL_TOKEN}" >/dev/null 2>&1; then
    ok=1
    break
  fi
  sleep 2
done
[[ "$ok" -eq 1 ]] || die "Pickup indisponível em ${PICKUP_BASE}/internal/health (token de $E2E_ENV_FILE)"

if [[ "${E2E_SKIP_GATEWAY}" != "1" ]]; then
  echo "[3/8] Health payment_gateway"
  curl -sfS "${GATEWAY_BASE}/health" >/dev/null || die "Gateway indisponível em ${GATEWAY_BASE}/health (ou use E2E_SKIP_GATEWAY=1)"
else
  echo "[3/8] Health payment_gateway (omitido E2E_SKIP_GATEWAY=1)"
fi

if [[ -z "${E2E_SLOT:-}" ]]; then
  E2E_SLOT="$(scan_free_slot)"
fi

E2E_USER_ID_FOR_SEED=""
if [[ -n "${E2E_USER_ID:-}" ]]; then
  E2E_USER_ID_FOR_SEED="${E2E_USER_ID//[:space:]/}"
elif [[ -n "${E2E_USER_EMAIL+set}" ]]; then
  if [[ -n "${E2E_USER_EMAIL}" ]]; then
    E2E_USER_ID_FOR_SEED="$(lookup_user_id_by_email "${E2E_USER_EMAIL}" || true)"
    if [[ -z "$E2E_USER_ID_FOR_SEED" ]]; then
      echo "AVISO: sem linha em users para E2E_USER_EMAIL='${E2E_USER_EMAIL}'; orders.user_id fica NULL." >&2
    fi
  fi
else
  _def_email="admin.operacao@ellanlab.com"
  E2E_USER_ID_FOR_SEED="$(lookup_user_id_by_email "${_def_email}" || true)"
  if [[ -z "$E2E_USER_ID_FOR_SEED" ]]; then
    echo "AVISO: utilizador lab '${_def_email}' não encontrado em users; orders.user_id fica NULL (crie o user ou defina E2E_USER_ID)." >&2
  fi
fi

echo "== E2E payment (run_id=$E2E_RUN_ID order=$ORDER_ID alloc=$ALLOC_ID slot=$E2E_SLOT locker=$LOCKER_ID skip_gateway=${E2E_SKIP_GATEWAY}) =="

echo "[4/8] Runtime allocate definitivo (slot=${E2E_SLOT}, allocation_id=${ALLOC_ID})"
code="$(http_allocate "${E2E_SLOT}" "${ALLOC_ID}")"
if [[ "$code" != "200" ]]; then
  die "allocate falhou (HTTP ${code}): $(cat /tmp/e2e_alloc_body.json 2>/dev/null)"
fi
head -c 300 /tmp/e2e_alloc_body.json
echo ""

echo "[5/8] psql seed (orders + allocations)"
psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -v ON_ERROR_STOP=1 \
  -v "order_id=${ORDER_ID}" \
  -v "allocation_id=${ALLOC_ID}" \
  -v "slot=${E2E_SLOT}" \
  -v "totem_id=${LOCKER_ID}" \
  -v "region=${E2E_REGION}" \
  -v "currency=${E2E_CURRENCY}" \
  -v "sku_id=${SKU_ID}" \
  -v "user_id=${E2E_USER_ID_FOR_SEED}" \
  -f "${ROOT_DIR}/02_docker/seeds/seed_e2e_payment_order.sql"

# P1: cartão no gateway → set_state PAID_PENDING_PICKUP no runtime (com X-Locker-Id no cliente HTTP).
GATEWAY_VALOR="$(python3 -c "print(round(int('${E2E_AMOUNT_CENTS}') / 100.0, 2))")"
E2E_TX_FALLBACK="e2e-tx-${E2E_RUN_ID}"
CONFIRM_TX="${E2E_TX_FALLBACK}"

if [[ "${E2E_SKIP_GATEWAY}" != "1" ]]; then
  echo "[6/8] POST ${GATEWAY_BASE}/gateway/payment/create (creditCard → runtime set-state)"
  python3 -c "import json; open('/tmp/e2e_gateway_body.json','w').write(json.dumps({
    'regiao': '${E2E_REGION}',
    'canal': 'ONLINE',
    'porta': int('${E2E_SLOT}'),
    'metodo': 'creditCard',
    'interface': 'api',
    'valor': float('${GATEWAY_VALOR}'),
    'currency': '${E2E_CURRENCY}',
    'locker_id': '${LOCKER_ID}',
    'order_id': '${ORDER_ID}',
  }))"
  gw_code="$(curl -sS -o /tmp/e2e_gateway_resp.json -w "%{http_code}" -X POST "${GATEWAY_BASE}/gateway/payment/create" \
    -H "Content-Type: application/json" \
    -H "Idempotency-Key: e2e-idem-${E2E_RUN_ID}" \
    -H "X-Device-Fingerprint: e2e-fp-${E2E_RUN_ID}" \
    -d @/tmp/e2e_gateway_body.json)"
  if [[ "$gw_code" != "200" ]]; then
    die "gateway payment/create HTTP ${gw_code}: $(head -c 600 /tmp/e2e_gateway_resp.json 2>/dev/null)"
  fi
  head -c 500 /tmp/e2e_gateway_resp.json
  echo ""
  GW_JSON="$(cat /tmp/e2e_gateway_resp.json)"
  export GW_JSON
  CONFIRM_TX="$(python3 -c 'import json,os; r=json.loads(os.environ["GW_JSON"]); assert r.get("result")=="approved", r; print(r.get("payment",{}).get("transaction_id") or "")')"
  [[ -n "$CONFIRM_TX" ]] || CONFIRM_TX="${E2E_TX_FALLBACK}"
else
  echo "[6/8] POST gateway (omitido E2E_SKIP_GATEWAY=1)"
fi

echo "[7/8] POST ${PICKUP_BASE}/internal/orders/${ORDER_ID}/payment-confirm"
RESP="$(curl -sfS -X POST "${PICKUP_BASE}/internal/orders/${ORDER_ID}/payment-confirm" \
  -H "Content-Type: application/json" \
  -H "X-Internal-Token: ${INTERNAL_TOKEN}" \
  -d "{\"order_id\":\"${ORDER_ID}\",\"region\":\"${E2E_REGION}\",\"totem_id\":\"${LOCKER_ID}\",\"channel\":\"ONLINE\",\"provider\":\"${E2E_PROVIDER}\",\"transaction_id\":\"${CONFIRM_TX}\",\"amount_cents\":${E2E_AMOUNT_CENTS},\"currency\":\"${E2E_CURRENCY}\"}")"

echo "$RESP" | head -c 800
echo ""

export RESP_JSON="$RESP"
python3 -c 'import json,os; r=json.loads(os.environ["RESP_JSON"]); assert r.get("ok") is True, r; assert r.get("status")=="PAID_PENDING_PICKUP", r' \
  || die "Resposta JSON inválida ou estado inesperado"

echo "[8/8] Postgres: order + allocation (status, payment_status, allocation.state)"
row="$(psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -v ON_ERROR_STOP=1 -t -A -c \
  "SELECT o.status::text || '|' || o.payment_status::text || '|' || a.state::text
   FROM orders o
   JOIN allocations a ON a.order_id = o.id AND a.id = '${ALLOC_ID}'
   WHERE o.id = '${ORDER_ID}';")"
exp="PAID_PENDING_PICKUP|APPROVED|RESERVED_PAID_PENDING_PICKUP"
[[ "$row" == "$exp" ]] || die "Postgres incoerente: esperado '${exp}', obtido '${row}'"

if [[ -n "${E2E_USER_ID_FOR_SEED}" ]]; then
  uchk="$(psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -v ON_ERROR_STOP=1 -t -A -c \
    "SELECT COALESCE(user_id::text, '') FROM orders WHERE id='${ORDER_ID}';" | tr -d '[:space:]')"
  [[ "$uchk" == "$E2E_USER_ID_FOR_SEED" ]] || die "orders.user_id esperado '${E2E_USER_ID_FOR_SEED}' obtido '${uchk}'"
fi

echo "OK: E2E payment (P1 gateway + pickup) concluído."
