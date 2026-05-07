#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${FRONTEND_PROXY_BASE_URL:-http://localhost}"

echo "=== Smoke: Frontend v0/v1 migration ==="
echo "BASE_URL=${BASE_URL}"

check_route() {
  local path="$1"
  local code
  code="$(curl -s -L -o /tmp/frontend_smoke_body.html -w "%{http_code}" "${BASE_URL}${path}")"
  if [[ "${code}" != "200" ]]; then
    echo "FAIL ${path}: HTTP ${code}" >&2
    exit 1
  fi
  echo "OK ${path}: HTTP ${code}"
}

check_route "/support"
check_route "/ops/health"
check_route "/fiscal"

echo "FRONTEND_V0_V1_SMOKE_OK"
