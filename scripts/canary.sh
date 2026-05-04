#!/usr/bin/env bash
set -euo pipefail

PARTNER_URL="${PARTNER_URL:-http://localhost:8002}"
OPS_URL="${OPS_URL:-http://localhost:8080}"
PROM="${PROMETHEUS_URL:-http://localhost:9090}"
SERVICE="${BASELINE_SERVICE:-order_pickup_service}"
ERR_THRESHOLD="${ERR_THRESHOLD:-0.005}"
WINDOW_MIN="${WINDOW_MIN:-5}"

echo "canary: POST pilot partner -> ${PARTNER_URL}/api/v1/partners"
curl -sfS -X POST "${PARTNER_URL}/api/v1/partners" \
  -H "Content-Type: application/json" \
  -d '{"name":"Canary","tier":"pilot"}' || true

echo "canary: monitor ${WINDOW_MIN}m error rate > ${ERR_THRESHOLD} -> rollback flags (USE_*=false via env/restart)"
deadline=$((SECONDS + WINDOW_MIN * 60))
while (( SECONDS < deadline )); do
  v=$(python3 - "$PROM" "$SERVICE" <<'PY'
import json, sys, urllib.parse, urllib.request
prom, job = sys.argv[1], sys.argv[2]
q = (
    f'sum(rate(http_requests_total{{job="{job}",status=~"5.."}}[5m])) '
    f'/ sum(rate(http_requests_total{{job="{job}"}}[5m]))'
)
url = prom.rstrip("/") + "/api/v1/query?" + urllib.parse.urlencode({"query": q})
try:
    with urllib.request.urlopen(url, timeout=10) as r:
        d = json.loads(r.read().decode())
    v = d.get("data", {}).get("result", [{}])[0].get("value", [None, None])[1]
    print(v or "")
except Exception:
    print("")
PY
)
  if [[ -n "$v" ]]; then
    python3 - "$v" "$ERR_THRESHOLD" <<'PY'
import sys
try:
    v, t = float(sys.argv[1]), float(sys.argv[2])
except ValueError:
    sys.exit(0)
sys.exit(1 if v > t else 0)
PY
    rc=$?
    if [[ "$rc" -eq 1 ]]; then
      echo "rollback: error rate $v > $ERR_THRESHOLD — set USE_PARTNER_SERVICE=false USE_INVENTORY_SERVICE=false USE_WALLET_SERVICE=false USE_LOGISTICS_SERVICE=false SHADOW_MODE_ENABLED=false and restart ${OPS_URL}"
      exit 2
    fi
  fi
  sleep 30
done
echo "canary: window complete, no rollback trigger"
exit 0
