#!/usr/bin/env bash
set -euo pipefail

OPS_BASE_URL="${OPS_BASE_URL:-http://localhost:8003}"
FISCAL_BASE_URL="${FISCAL_BASE_URL:-http://localhost:8020}"
DEFAULT_ENV_FILE="/home/marcos/ellan_lab/02_docker/.env"
LOG_DIR="/home/marcos/ellan_lab/04_logs/ops"
TIMESTAMP_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
JSON_ENABLED="false"
ENV_FILE=""
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
    --env-file)
      ENV_FILE="${2:-}"
      if [[ -z "${ENV_FILE}" ]]; then
        echo "ERROR: --env-file exige um caminho de arquivo." >&2
        exit 1
      fi
      shift 2
      ;;
    *)
      if [[ -z "${ENV_FILE}" ]]; then
        ENV_FILE="$1"
        shift
      else
        echo "ERROR: argumento não reconhecido: $1" >&2
        exit 1
      fi
      ;;
  esac
done

if [[ -z "${ENV_FILE}" ]]; then
  ENV_FILE="${DEFAULT_ENV_FILE}"
fi

read_env() {
  local key="$1"
  local file="$2"
  python3 - "$key" "$file" <<'PY'
import sys
key, path = sys.argv[1], sys.argv[2]
try:
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() == key:
                print(v.strip())
                break
except FileNotFoundError:
    pass
PY
}

OPS_TOKEN="${OPS_TOKEN:-}"
INTERNAL_TOKEN="${INTERNAL_TOKEN:-}"

if [[ -z "${OPS_TOKEN}" && -f "${ENV_FILE}" ]]; then
  OPS_TOKEN="$(read_env "OPS_TOKEN" "${ENV_FILE}")"
fi
if [[ -z "${INTERNAL_TOKEN}" && -f "${ENV_FILE}" ]]; then
  INTERNAL_TOKEN="$(read_env "ORDER_INTERNAL_TOKEN" "${ENV_FILE}")"
fi

if [[ -z "${OPS_TOKEN}" ]]; then
  echo "ERROR: OPS_TOKEN ausente (env/arquivo)." >&2
  exit 1
fi
if [[ -z "${INTERNAL_TOKEN}" ]]; then
  echo "ERROR: INTERNAL_TOKEN ausente (env/arquivo)." >&2
  exit 1
fi

echo "== OPS SANITY =="
echo "ENV_FILE=${ENV_FILE}"
echo "OPS_BASE_URL=${OPS_BASE_URL}"
echo "FISCAL_BASE_URL=${FISCAL_BASE_URL}"
echo

fail=0
CHECK_RESULTS=""
run_check() {
  local label="$1"
  local url="$2"
  local header_name="$3"
  local header_val="$4"
  local out_file="$5"
  local code
  code="$(curl -s -o "${out_file}" -w "%{http_code}" "${url}" -H "${header_name}: ${header_val}")"
  local status="OK"
  if [[ "${code}" == "200" ]]; then
    echo "[OK] ${label} -> ${code}"
  else
    echo "[ERRO] ${label} -> ${code}"
    fail=$((fail + 1))
    status="ERRO"
  fi
  CHECK_RESULTS+="${label}|${status}|${code}|${url}|${out_file}"$'\n'
}

run_check \
  "OPS top-divergences" \
  "${OPS_BASE_URL}/partners/ops/settlements/reconciliation/top-divergences?top_n=3" \
  "Authorization" "Bearer ${OPS_TOKEN}" \
  "/tmp/ops_sanity_top_div.json"

run_check \
  "OPS outbox" \
  "${OPS_BASE_URL}/ops/integration/order-events-outbox?limit=3" \
  "Authorization" "Bearer ${OPS_TOKEN}" \
  "/tmp/ops_sanity_outbox.json"

run_check \
  "OPS dead-letter-priority" \
  "${OPS_BASE_URL}/ops/integration/order-events-outbox/dead-letter-priority?limit=3" \
  "Authorization" "Bearer ${OPS_TOKEN}" \
  "/tmp/ops_sanity_deadletter.json"

run_check \
  "Fiscal providers/status" \
  "${FISCAL_BASE_URL}/admin/fiscal/providers/status" \
  "X-Internal-Token" "${INTERNAL_TOKEN}" \
  "/tmp/ops_sanity_fiscal_status.json"

run_check \
  "Fiscal BR gate" \
  "${FISCAL_BASE_URL}/admin/fiscal/providers/br-go-no-go?run_connectivity=true" \
  "X-Internal-Token" "${INTERNAL_TOKEN}" \
  "/tmp/ops_sanity_fiscal_br_gate.json"

run_check \
  "Fiscal PT gate" \
  "${FISCAL_BASE_URL}/admin/fiscal/providers/pt-go-no-go?run_connectivity=true" \
  "X-Internal-Token" "${INTERNAL_TOKEN}" \
  "/tmp/ops_sanity_fiscal_pt_gate.json"

echo
FINAL_RESULT="OPS_SANITY_OK"
if [[ ${fail} -eq 0 ]]; then
  echo "RESULTADO FINAL: OPS_SANITY_OK"
else
  FINAL_RESULT="OPS_SANITY_FAIL"
  echo "RESULTADO FINAL: OPS_SANITY_FAIL (${fail} checks com erro)"
fi

if [[ "${JSON_ENABLED}" == "true" ]]; then
  mkdir -p "${LOG_DIR}"
  if [[ -z "${JSON_PATH}" ]]; then
    JSON_PATH="${LOG_DIR}/ops_sanity_${TIMESTAMP_UTC}.json"
  fi
  python3 - "${JSON_PATH}" "${LOG_DIR}/ops_sanity_latest.json" "${FINAL_RESULT}" "${fail}" "${ENV_FILE}" "${OPS_BASE_URL}" "${FISCAL_BASE_URL}" "${CHECK_RESULTS}" <<'PY'
import json
import pathlib
import shutil
import sys
from datetime import datetime, timezone

json_path = pathlib.Path(sys.argv[1])
latest_path = pathlib.Path(sys.argv[2])
final_result = sys.argv[3]
fail_count = int(sys.argv[4])
env_file = sys.argv[5]
ops_base_url = sys.argv[6]
fiscal_base_url = sys.argv[7]
raw_checks = sys.argv[8]

checks = []
for line in raw_checks.splitlines():
    if not line.strip():
        continue
    label, status, code, url, out_file = line.split("|", 4)
    body = None
    try:
        body = json.loads(pathlib.Path(out_file).read_text(encoding="utf-8"))
    except Exception:
        body = {"raw": pathlib.Path(out_file).read_text(encoding="utf-8", errors="ignore")}
    checks.append(
        {
            "label": label,
            "status": status,
            "http_code": int(code),
            "url": url,
            "body": body,
        }
    )

payload = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "result": final_result,
    "fail_count": fail_count,
    "env_file": env_file,
    "ops_base_url": ops_base_url,
    "fiscal_base_url": fiscal_base_url,
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
