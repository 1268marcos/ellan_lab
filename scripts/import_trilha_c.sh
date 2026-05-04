#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT_G="${GRAFANA_DASHBOARDS_DIR:-${ROOT}/.grafana-dashboards}"
OUT_R="${RUNBOOKS_IMPORT_DIR:-${ROOT}/.imported-runbooks}"
mkdir -p "$OUT_G" "$OUT_R"
cp "${ROOT}/dashboards/migration.json" "$OUT_G/"
cp "${ROOT}/runbooks/"*.md "$OUT_R/"
echo "import_trilha_c: migration.json + runbooks -> ${OUT_G} , ${OUT_R}"
