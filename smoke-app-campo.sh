#!/bin/bash
set -e

# Smoke test para App Campo MVP
RUNTIME_BASE_URL="${RUNTIME_BASE_URL:-http://localhost:8200}"

curl -fsS "${RUNTIME_BASE_URL}/health" || exit 1
curl -fsS "${RUNTIME_BASE_URL}/api/v1/field/health" || exit 1
echo "App Campo smoke OK"
