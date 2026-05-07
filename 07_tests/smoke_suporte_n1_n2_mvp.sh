#!/usr/bin/env bash
set -euo pipefail

ORDER_PICKUP_BASE_URL="${ORDER_PICKUP_BASE_URL:-http://localhost:8003}"
ORDER_ID="${ORDER_ID:-ORDER-MVP-001}"

echo "=== Smoke: Suporte N1/N2 MVP ==="
echo "ORDER_PICKUP_BASE_URL=${ORDER_PICKUP_BASE_URL}"

curl -fsS "${ORDER_PICKUP_BASE_URL}/api/v1/support/health" | python3 -m json.tool >/tmp/support_health.json
curl -fsS "${ORDER_PICKUP_BASE_URL}/api/v1/support/order/${ORDER_ID}" | python3 -m json.tool >/tmp/support_order.json

python3 - <<'PY'
import json
from pathlib import Path

health = json.loads(Path("/tmp/support_health.json").read_text())
order = json.loads(Path("/tmp/support_order.json").read_text())

assert health["status"] == "ok"
assert "status" in order
assert isinstance(order["timeline"], list)
print("SUPORTE_N1_N2_SMOKE_OK")
PY
