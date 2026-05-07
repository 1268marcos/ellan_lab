#!/usr/bin/env bash
set -euo pipefail

echo "=== Smoke: Fiscal MVP ==="

bash 02_docker/run_fiscal_routes_smoke.sh

if [[ -f 01_source/backend/billing_fiscal_service/config/fiscal_flags.json ]]; then
  if command -v jq >/dev/null 2>&1; then
    jq -e '.global.default_provider == "stub" and .global.audit_fallback == true' \
      01_source/backend/billing_fiscal_service/config/fiscal_flags.json >/dev/null
  else
    python3 - <<'PY'
import json
from pathlib import Path

flags = json.loads(Path("01_source/backend/billing_fiscal_service/config/fiscal_flags.json").read_text())
assert flags["global"]["default_provider"] == "stub"
assert flags["global"]["audit_fallback"] is True
PY
  fi
fi

echo "FISCAL_MVP_SMOKE_OK"
