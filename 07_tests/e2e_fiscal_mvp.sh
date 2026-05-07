#!/usr/bin/env bash
set -euo pipefail

echo "=== E2E placeholder: Fiscal MVP ==="
echo "Fluxo alvo: order paid -> invoice -> provider/fallback -> callback/reconciliation evidence."
bash 07_tests/smoke_fiscal_mvp.sh
echo "E2E_FISCAL_MVP_PLACEHOLDER_OK"
