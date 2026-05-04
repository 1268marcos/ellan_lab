#!/usr/bin/env bash
set -euo pipefail
check() {
  local base="$1"
  curl -sf "${base%/}/health/ready" >/dev/null
  curl -sf "${base%/}/health/live" >/dev/null
}
OPS="${ORDER_PICKUP_BASE_URL:-http://127.0.0.1:8000}"
WAL="${WALLET_SERVICE_BASE_URL:-http://127.0.0.1:8004}"
LOG="${LOGISTICS_SERVICE_BASE_URL:-http://127.0.0.1:8005}"
check "$OPS"
check "$WAL"
check "$LOG"
echo "validate_cleanup: /health/ready + /health/live OK"
