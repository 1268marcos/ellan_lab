#!/usr/bin/env bash
set -euo pipefail

REPORT="docs/regression_final_report.md"
PASSED=0
FAILED=0

mkdir -p "$(dirname "$REPORT")"

echo "# Regression Final Report - $(date)" > "$REPORT"
echo "" >> "$REPORT"

run_test() {
    local name="$1"
    local command="$2"
    echo "### $name" >> "$REPORT"
    echo '```bash' >> "$REPORT"
    echo "$ $command" >> "$REPORT"
    if ( eval "$command" ) >> "$REPORT" 2>&1; then
        echo "PASS" >> "$REPORT"
        PASSED=$((PASSED + 1))
    else
        echo "FAIL" >> "$REPORT"
        FAILED=$((FAILED + 1))
    fi
    echo '```' >> "$REPORT"
    echo "" >> "$REPORT"
}

run_test "Frontend Build" "cd 01_source/frontend && npm run build"
run_test "Frontend_v0 Build" "cd 01_source/frontend_v0 && npm run build"
run_test "App Campo Smoke" "./smoke-app-campo.sh"
run_test "NOC Smoke" "./smoke-noc.sh"
run_test "Suporte Smoke" "./smoke-suporte.sh"
run_test "Fiscal Smoke" "./smoke-fiscal.sh"
run_test "Proxy v0/v1" "curl -fsSI http://localhost:5180/ | sed -n '1p'"
run_test "E2E App Campo" "bash 07_tests/e2e_app_campo_mvp.sh"
run_test "E2E NOC" "bash 07_tests/e2e_noc_simt_mvp.sh"
run_test "E2E Suporte" "bash 07_tests/e2e_suporte_n1_n2_mvp.sh"
run_test "E2E Offline Sync" "bash 07_tests/e2e_offline_sync.sh"
run_test "Fiscal Go/No-Go" "bash 02_docker/run_f3_go_no_go.sh"

echo "## Resumo" >> "$REPORT"
echo "- **Passed:** $PASSED" >> "$REPORT"
echo "- **Failed:** $FAILED" >> "$REPORT"
echo "- **Total:** $((PASSED + FAILED))" >> "$REPORT"

if [ "$FAILED" -eq 0 ]; then
    echo "**FINAL RESULT: ALL TESTS PASSED**" >> "$REPORT"
    echo "ALL TESTS PASSED"
else
    echo "**FINAL RESULT: $FAILED TESTS FAILED**" >> "$REPORT"
    echo "$FAILED TESTS FAILED"
    exit 1
fi
