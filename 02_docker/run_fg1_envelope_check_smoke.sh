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

echo "== FG1 ENVELOPE CHECK SMOKE =="
echo "ENV_FILE=${ENV_FILE}"
echo "FISCAL_BASE_URL=${FISCAL_BASE_URL}"
echo

OUT="/tmp/fg1_envelope_check_smoke.json"
HTTP_CODE="$(curl -sS -o "${OUT}" -w "%{http_code}" "${FISCAL_BASE_URL}/admin/fiscal/global/fg1/envelope-check" -H "X-Internal-Token: ${INTERNAL_TOKEN}" -H "Accept: application/json")"

FAIL_COUNT=0
FINAL_RESULT="FG1_ENVELOPE_CHECK_SMOKE_OK"
REASON="ok"
if [[ "${HTTP_CODE}" != "200" ]]; then
  FAIL_COUNT=1
  FINAL_RESULT="FG1_ENVELOPE_CHECK_SMOKE_FAIL"
  REASON="http_${HTTP_CODE}"
fi

python3 - "${OUT}" "${HTTP_CODE}" "${FINAL_RESULT}" "${REASON}" <<'PY'
import json
import pathlib
import sys
payload = {}
raw = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8", errors="ignore")
try:
    payload = json.loads(raw)
except Exception:
    payload = {"raw": raw}
summary = {
    "http_code": int(sys.argv[2]),
    "result": sys.argv[3],
    "reason": sys.argv[4],
    "status": payload.get("status"),
    "error_count": payload.get("error_count"),
    "checked_pairs": payload.get("checked_pairs"),
}
print(json.dumps({"summary": summary}, ensure_ascii=False))
PY

if [[ "${JSON_ENABLED}" == "true" ]]; then
  mkdir -p "${LOG_DIR}"
  if [[ -z "${JSON_PATH}" ]]; then
    JSON_PATH="${LOG_DIR}/fg1_envelope_check_smoke_${TIMESTAMP_UTC}.json"
  fi
  python3 - "${OUT}" "${JSON_PATH}" "${LOG_DIR}/fg1_envelope_check_smoke_latest.json" "${FINAL_RESULT}" "${FAIL_COUNT}" "${REASON}" "${HTTP_CODE}" "${FISCAL_BASE_URL}" "${ENV_FILE}" <<'PY'
import json
import pathlib
import shutil
import sys
from datetime import datetime, timezone

out = pathlib.Path(sys.argv[1])
json_path = pathlib.Path(sys.argv[2])
latest_path = pathlib.Path(sys.argv[3])
payload = {}
raw = out.read_text(encoding="utf-8", errors="ignore")
try:
    payload = json.loads(raw)
except Exception:
    payload = {"raw": raw}
result = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "result": sys.argv[4],
    "fail_count": int(sys.argv[5]),
    "reason": sys.argv[6],
    "http_code": int(sys.argv[7]),
    "fiscal_base_url": sys.argv[8],
    "env_file": sys.argv[9],
    "summary": {
        "status": payload.get("status"),
        "error_count": payload.get("error_count"),
        "checked_pairs": payload.get("checked_pairs"),
        "check_version": payload.get("check_version"),
    },
    "payload": payload,
}
json_path.parent.mkdir(parents=True, exist_ok=True)
json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
shutil.copyfile(json_path, latest_path)
print(f"JSON_EXPORT={json_path}")
print(f"JSON_LATEST={latest_path}")
PY
fi

echo
if [[ ${FAIL_COUNT} -eq 0 ]]; then
  echo "RESULTADO FINAL: FG1_ENVELOPE_CHECK_SMOKE_OK"
  exit 0
fi
echo "RESULTADO FINAL: FG1_ENVELOPE_CHECK_SMOKE_FAIL (${REASON})"
exit 2
