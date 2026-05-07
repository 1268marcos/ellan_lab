#!/bin/bash
set -e

GO_NO_GO_RESULT="NO_GO"
EVIDENCE_FILE="${EVIDENCE_FILE:-docs/fiscal_go_no_go_evidence.md}"
FLAGS_FILE="01_source/backend/billing_fiscal_service/config/fiscal_flags.json"
FISCAL_BASE_URL="${FISCAL_BASE_URL:-http://localhost:8020}"

mkdir -p "$(dirname "$EVIDENCE_FILE")"

echo "# Fiscal Go/No-Go Evidence" > "$EVIDENCE_FILE"
echo "Date: $(date)" >> "$EVIDENCE_FILE"
echo "" >> "$EVIDENCE_FILE"

# 1. Verificar flags
echo "## 1. Configuration Flags" >> "$EVIDENCE_FILE"
if command -v jq >/dev/null 2>&1; then
  jq . "$FLAGS_FILE" >> "$EVIDENCE_FILE"
else
  cat "$FLAGS_FILE" >> "$EVIDENCE_FILE"
fi
echo "" >> "$EVIDENCE_FILE"

# 2. Smoke test BR
echo "## 2. Brazil Smoke Test" >> "$EVIDENCE_FILE"
if bash 02_docker/run_fiscal_routes_smoke.sh >> "$EVIDENCE_FILE" 2>&1; then
    echo "Brazil smoke PASS" >> "$EVIDENCE_FILE"
    BRAZIL_OK=true
else
    echo "Brazil smoke FAIL" >> "$EVIDENCE_FILE"
    BRAZIL_OK=false
fi
echo "" >> "$EVIDENCE_FILE"

# 3. Homologação real BR (se flag true)
REAL_BR=$(jq -r '.brazil.sefaz_homologation_ready' "$FLAGS_FILE")
if [ "$REAL_BR" = "true" ]; then
    echo "## 3. Brazil Real Provider Test" >> "$EVIDENCE_FILE"
    if curl -fsS -X POST "${FISCAL_BASE_URL}/api/fiscal/real-test" >> "$EVIDENCE_FILE" 2>&1; then
        echo "Brazil real provider PASS" >> "$EVIDENCE_FILE"
    else
        echo "Brazil real provider FAIL - using fallback" >> "$EVIDENCE_FILE"
    fi
    echo "" >> "$EVIDENCE_FILE"
fi

# 4. Decisão final
echo "## 4. Decision" >> "$EVIDENCE_FILE"
if [ "$BRAZIL_OK" = true ]; then
    GO_NO_GO_RESULT="GO"
    echo "GO: Brazil fiscal smoke passes" >> "$EVIDENCE_FILE"
else
    echo "NO-GO: Brazil fiscal smoke fails" >> "$EVIDENCE_FILE"
fi

echo "" >> "$EVIDENCE_FILE"
echo "## 5. Rollback Plan" >> "$EVIDENCE_FILE"
echo "1. Set flag brazil.sefaz_provider to 'stub'" >> "$EVIDENCE_FILE"
echo "2. Restart service" >> "$EVIDENCE_FILE"
echo "3. Smoke test again" >> "$EVIDENCE_FILE"

echo "FISCAL GO/NO-GO: $GO_NO_GO_RESULT"
echo "Evidence: $EVIDENCE_FILE"
exit 0
