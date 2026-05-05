#!/usr/bin/env bash
set -euo pipefail

export MOCK_BILLING=true

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BILLING_PORT="${BILLING_MOCK_PORT:-18020}"
export BILLING_SERVICE_PROXY="http://127.0.0.1:${BILLING_PORT}"

VITE_PORT="${VITE_TEST_PORT:-5187}"

VITE_PID=""
MOCK_PID=""

cleanup() {
  if [[ -n "$VITE_PID" ]] && kill -0 "$VITE_PID" 2>/dev/null; then
    kill "$VITE_PID" 2>/dev/null || true
    wait "$VITE_PID" 2>/dev/null || true
  fi
  if [[ -n "$MOCK_PID" ]] && kill -0 "$MOCK_PID" 2>/dev/null; then
    kill "$MOCK_PID" 2>/dev/null || true
    wait "$MOCK_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

python3 -u - "$BILLING_PORT" <<'PY' &
import json, sys
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if "/v1/billing/cycles" in self.path:
            body = json.dumps(
                {
                    "items": [
                        {
                            "id": "mock-cycle-1",
                            "period_start": "2024-01-01",
                            "period_end": "2024-01-31",
                            "status": "OPEN",
                            "total_amount_cents": 10000,
                        }
                    ]
                }
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"detail":"not found"}')

    def log_message(self, *args):
        pass

port = int(sys.argv[1])
HTTPServer(("127.0.0.1", port), H).serve_forever()
PY
MOCK_PID=$!

echo "[test-billing] MOCK_BILLING=$MOCK_BILLING mock PID=$MOCK_PID :$BILLING_PORT"

for _ in $(seq 1 50); do
  if curl -sf "http://127.0.0.1:${BILLING_PORT}/v1/billing/cycles?partner_id=test" | grep -q "mock-cycle-1"; then
    break
  fi
  sleep 0.1
done
curl -sf "http://127.0.0.1:${BILLING_PORT}/v1/billing/cycles?partner_id=test" | grep -q "mock-cycle-1"

npm run dev -- --host 127.0.0.1 --port "$VITE_PORT" --strictPort --clearScreen false &
VITE_PID=$!

echo "[test-billing] vite PID=$VITE_PID :$VITE_PORT"

for _ in $(seq 1 100); do
  if curl -sf "http://127.0.0.1:${VITE_PORT}/" >/dev/null; then
    break
  fi
  sleep 0.1
done
curl -sf "http://127.0.0.1:${VITE_PORT}/" >/dev/null

PROXY_URL="http://127.0.0.1:${VITE_PORT}/api/billing-svc/v1/billing/cycles?partner_id=test-partner"
RESP="$(curl -sf "$PROXY_URL")"
export RESP
echo "[test-billing] proxy response: ${RESP:0:120}..."

python3 - <<'PY'
import json, os
raw = os.environ["RESP"]
d = json.loads(raw)
items = d.get("items") if isinstance(d, dict) else None
assert isinstance(items, list) and len(items) >= 1, d
row = items[0]
assert row.get("id") == "mock-cycle-1"
assert row.get("status") == "OPEN"
assert row.get("total_amount_cents") == 10000
PY

HTML="$(curl -sf "http://127.0.0.1:${VITE_PORT}/finance/billing/cycles")"
echo "$HTML" | grep -q 'id="root"'

echo "[test-billing] proxy JSON + SPA shell OK"
