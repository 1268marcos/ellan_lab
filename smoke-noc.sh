#!/bin/bash
set -e

RUNTIME_BASE_URL="${RUNTIME_BASE_URL:-http://localhost:8200}"
LIFECYCLE_BASE_URL="${LIFECYCLE_BASE_URL:-http://localhost:8010}"

curl -fsS "${LIFECYCLE_BASE_URL}/health" || exit 1
curl -fsS "${LIFECYCLE_BASE_URL}/api/v1/noc/health" || exit 1
curl -fsS "${RUNTIME_BASE_URL}/api/v1/noc/health" || exit 1
echo "NOC smoke OK"
