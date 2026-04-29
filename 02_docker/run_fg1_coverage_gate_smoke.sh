#!/usr/bin/env bash
set -euo pipefail

FISCAL_BASE_URL="${FISCAL_BASE_URL:-http://localhost:8020}"
DEFAULT_ENV_FILE="/home/marcos/ellan_lab/02_docker/.env"
LOG_DIR="/home/marcos/ellan_lab/04_logs/ops"
TIMESTAMP_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
JSON_ENABLED="false"
JSON_PATH=""
ENV_FILE=""

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

INTERNAL_TOKEN="${INTERNAL_TOKEN:-}"
if [[ -z "${INTERNAL_TOKEN}" && -f "${ENV_FILE}" ]]; then
  INTERNAL_TOKEN="$(read_env "ORDER_INTERNAL_TOKEN" "${ENV_FILE}")"
fi

if [[ -z "${INTERNAL_TOKEN}" ]]; then
  echo "ERROR: INTERNAL_TOKEN ausente (env/arquivo)." >&2
  exit 1
fi

echo "== FG1 COVERAGE GATE SMOKE =="
echo "ENV_FILE=${ENV_FILE}"
echo "FISCAL_BASE_URL=${FISCAL_BASE_URL}"
echo

OUT_FILE="/tmp/fg1_coverage_gate_smoke.json"
HTTP_CODE="$(curl -sS -o "${OUT_FILE}" -w "%{http_code}" "${FISCAL_BASE_URL}/admin/fiscal/global/fg1/coverage-gate" -H "X-Internal-Token: ${INTERNAL_TOKEN}" -H "Accept: application/json")"

FAIL_COUNT=0
FINAL_RESULT="FG1_COVERAGE_GATE_SMOKE_OK"
REASON="ok"
if [[ "${HTTP_CODE}" != "200" ]]; then
  FAIL_COUNT=1
  FINAL_RESULT="FG1_COVERAGE_GATE_SMOKE_FAIL"
  REASON="http_${HTTP_CODE}"
fi

python3 - "${OUT_FILE}" "${HTTP_CODE}" "${FINAL_RESULT}" "${REASON}" <<'PY'
import json
import pathlib
import sys

out_file = pathlib.Path(sys.argv[1])
http_code = int(sys.argv[2])
result = sys.argv[3]
reason = sys.argv[4]
raw = out_file.read_text(encoding="utf-8", errors="ignore")
payload = {}
try:
    payload = json.loads(raw)
except Exception:
    payload = {"raw": raw}

summary = {
    "http_code": http_code,
    "result": result,
    "reason": reason,
    "decision": payload.get("decision"),
    "missing_scenarios_total": payload.get("missing_scenarios_total"),
    "country_count": payload.get("country_count"),
    "required_scenarios_total": payload.get("required_scenarios_total"),
    "gate_version": payload.get("gate_version"),
}
print(json.dumps({"summary": summary}, ensure_ascii=False))
PY

if [[ "${JSON_ENABLED}" == "true" ]]; then
  mkdir -p "${LOG_DIR}"
  if [[ -z "${JSON_PATH}" ]]; then
    JSON_PATH="${LOG_DIR}/fg1_coverage_gate_smoke_${TIMESTAMP_UTC}.json"
  fi
  python3 - "${OUT_FILE}" "${JSON_PATH}" "${LOG_DIR}/fg1_coverage_gate_smoke_latest.json" "${FINAL_RESULT}" "${FAIL_COUNT}" "${REASON}" "${HTTP_CODE}" "${FISCAL_BASE_URL}" "${ENV_FILE}" <<'PY'
import json
import pathlib
import shutil
import sys
from datetime import datetime, timezone

raw_file = pathlib.Path(sys.argv[1])
json_path = pathlib.Path(sys.argv[2])
latest_path = pathlib.Path(sys.argv[3])
final_result = sys.argv[4]
fail_count = int(sys.argv[5])
reason = sys.argv[6]
http_code = int(sys.argv[7])
fiscal_base_url = sys.argv[8]
env_file = sys.argv[9]

raw = raw_file.read_text(encoding="utf-8", errors="ignore")
body = {}
try:
    body = json.loads(raw)
except Exception:
    body = {"raw": raw}

payload = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "result": final_result,
    "fail_count": fail_count,
    "reason": reason,
    "http_code": http_code,
    "fiscal_base_url": fiscal_base_url,
    "env_file": env_file,
    "summary": {
        "decision": body.get("decision"),
        "missing_scenarios_total": body.get("missing_scenarios_total"),
        "country_count": body.get("country_count"),
        "required_scenarios_total": body.get("required_scenarios_total"),
        "gate_version": body.get("gate_version"),
    },
    "payload": body,
}
json_path.parent.mkdir(parents=True, exist_ok=True)
json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
shutil.copyfile(json_path, latest_path)
print(f"JSON_EXPORT={json_path}")
print(f"JSON_LATEST={latest_path}")
PY
fi

echo
if [[ ${FAIL_COUNT} -eq 0 ]]; then
  echo "RESULTADO FINAL: FG1_COVERAGE_GATE_SMOKE_OK"
  exit 0
fi
echo "RESULTADO FINAL: FG1_COVERAGE_GATE_SMOKE_FAIL (${REASON})"
exit 2
