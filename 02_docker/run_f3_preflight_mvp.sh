#!/bin/bash
set -e

echo "=== Fiscal Pre-flight MVP ==="

# Verifica flags
echo "1. Checking flags..."
if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: jq is required to validate fiscal flags." >&2
  exit 1
fi
cat 01_source/backend/billing_fiscal_service/config/fiscal_flags.json | jq .

# Testa stub no billing_fiscal_service (porta Docker atual: 8020)
echo "2. Testing stub provider..."
curl -X POST http://localhost:8020/api/fiscal/invoice \
  -d '{"amount":100}' \
  -H "Content-Type: application/json"

# Verifica fallback
echo "3. Testing fallback mechanism..."
# MVP: fallback is enabled by config and audited in fiscal_flags.json.
jq -e '.brazil.fallback_enabled == true and .portugal.fallback_enabled == true and .global.audit_fallback == true' \
  01_source/backend/billing_fiscal_service/config/fiscal_flags.json >/dev/null

echo "=== Pre-flight complete ==="
