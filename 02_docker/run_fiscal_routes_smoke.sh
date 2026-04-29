#!/usr/bin/env bash
set -euo pipefail

FRONTEND_BASE_URL="${FRONTEND_BASE_URL:-http://localhost:5173}"
LOG_DIR="/home/marcos/ellan_lab/04_logs/ops"
TIMESTAMP_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
JSON_ENABLED="false"
JSON_PATH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --json)
      JSON_ENABLED="true"
      shift
      ;;
    --json-path)
      JSON_ENABLED="true"
      JSON_PATH="${2:-}"
      if [[ -z "${JSON_PATH}" ]]; then
        echo "ERROR: --json-path exige um caminho de arquivo." >&2
        exit 1
      fi
      shift 2
      ;;
    *)
      echo "ERROR: argumento não reconhecido: $1" >&2
      exit 1
      ;;
  esac
done

echo "== FISCAL ROUTES SMOKE =="
echo "FRONTEND_BASE_URL=${FRONTEND_BASE_URL}"
echo

fail=0
CHECK_RESULTS=""

run_route_check() {
  local label="$1"
  local route_path="$2"
  local must_contain="$3"
  local out_file="$4"

  local full_url="${FRONTEND_BASE_URL}${route_path}"
  local http_code
  http_code="$(curl -s -L -o "${out_file}" -w "%{http_code}" "${full_url}")"
  local body
  body="$(tr -d '\000' < "${out_file}")"

  local status="OK"
  local reason="ok"
  local marker_found="true"
  if [[ "${http_code}" != "200" ]]; then
    status="ERRO"
    reason="http_${http_code}"
    fail=$((fail + 1))
  elif [[ "${body}" == *"Not Found"* ]]; then
    status="ERRO"
    reason="contains_not_found"
    fail=$((fail + 1))
  elif [[ "${body}" != *"${must_contain}"* ]]; then
    marker_found="false"
    reason="ok_marker_not_detected_spa"
  fi

  if [[ "${status}" == "OK" ]]; then
    if [[ "${marker_found}" == "true" ]]; then
      echo "[OK] ${label} -> ${http_code}"
    else
      echo "[OK] ${label} -> ${http_code} (marker não detectado via curl em SPA)"
    fi
  else
    echo "[ERRO] ${label} -> ${http_code} (${reason})"
  fi

  CHECK_RESULTS+="${label}|${status}|${http_code}|${reason}|${marker_found}|${full_url}|${out_file}"$'\n'
}

run_route_check \
  "FISCAL global" \
  "/fiscal" \
  "FISCAL - Catálogo Global" \
  "/tmp/fiscal_routes_smoke_global.html"

run_route_check \
  "FISCAL updates" \
  "/fiscal/updates" \
  "FISCAL - Updates" \
  "/tmp/fiscal_routes_smoke_updates.html"

run_route_check \
  "FISCAL countries" \
  "/fiscal/countries" \
  "FISCAL - Countries Cockpit (FG-1/FG-2)" \
  "/tmp/fiscal_routes_smoke_countries.html"

echo
FINAL_RESULT="FISCAL_ROUTES_SMOKE_OK"
if [[ ${fail} -eq 0 ]]; then
  echo "RESULTADO FINAL: FISCAL_ROUTES_SMOKE_OK"
else
  FINAL_RESULT="FISCAL_ROUTES_SMOKE_FAIL"
  echo "RESULTADO FINAL: FISCAL_ROUTES_SMOKE_FAIL (${fail} rota(s) com erro)"
fi

if [[ "${JSON_ENABLED}" == "true" ]]; then
  mkdir -p "${LOG_DIR}"
  if [[ -z "${JSON_PATH}" ]]; then
    JSON_PATH="${LOG_DIR}/fiscal_routes_smoke_${TIMESTAMP_UTC}.json"
  fi
  python3 - "${JSON_PATH}" "${LOG_DIR}/fiscal_routes_smoke_latest.json" "${FINAL_RESULT}" "${fail}" "${FRONTEND_BASE_URL}" "${CHECK_RESULTS}" <<'PY'
import json
import pathlib
import shutil
import sys
from datetime import datetime, timezone

json_path = pathlib.Path(sys.argv[1])
latest_path = pathlib.Path(sys.argv[2])
final_result = sys.argv[3]
fail_count = int(sys.argv[4])
frontend_base_url = sys.argv[5]
raw_checks = sys.argv[6]

checks = []
for line in raw_checks.splitlines():
    if not line.strip():
        continue
    label, status, code, reason, marker_found, url, out_file = line.split("|", 6)
    body_preview = pathlib.Path(out_file).read_text(encoding="utf-8", errors="ignore")[:500]
    checks.append(
        {
            "label": label,
            "status": status,
            "http_code": int(code),
            "reason": reason,
            "expected_marker_found_in_raw_html": marker_found == "true",
            "url": url,
            "body_preview": body_preview,
        }
    )

payload = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "result": final_result,
    "fail_count": fail_count,
    "frontend_base_url": frontend_base_url,
    "checks": checks,
}

json_path.parent.mkdir(parents=True, exist_ok=True)
json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
shutil.copyfile(json_path, latest_path)
print(f"JSON_EXPORT={json_path}")
print(f"JSON_LATEST={latest_path}")
PY
fi

if [[ ${fail} -eq 0 ]]; then
  exit 0
fi
exit 2
