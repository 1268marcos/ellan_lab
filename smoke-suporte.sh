#!/bin/bash
set -e

ORDER_PICKUP_BASE_URL="${ORDER_PICKUP_BASE_URL:-http://localhost:8003}"

curl -fsS "${ORDER_PICKUP_BASE_URL}/health" || exit 1
curl -fsS "${ORDER_PICKUP_BASE_URL}/api/v1/support/health" || exit 1
echo "Suporte smoke OK"
