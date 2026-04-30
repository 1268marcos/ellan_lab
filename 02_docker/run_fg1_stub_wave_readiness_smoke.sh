#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BILLING_FISCAL_BASE_URL:-http://localhost:8020}"
TOKEN="${INTERNAL_TOKEN:-}"
AS_JSON="0"
DEFAULT_ENV_FILE="/home/marcos/ellan_lab/02_docker/.env"
ENV_FILE=""
JSON_PATH=""

for arg in "$@"; do
  case "$arg" in
    --json) AS_JSON="1" ;;
  esac
done

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

while [[ $# -gt 0 ]]; do
  case "$1" in
    --json)
      shift
      ;;
    --json-path)
      AS_JSON="1"
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

if [[ -z "${TOKEN}" && -f "${ENV_FILE}" ]]; then
  TOKEN="$(read_env "ORDER_INTERNAL_TOKEN" "${ENV_FILE}")"
fi

if [[ -z "${TOKEN}" ]]; then
  echo "ERROR: INTERNAL_TOKEN não definido." >&2
  exit 2
fi

TMP_FILE="$(mktemp)"
HTTP_CODE="$(curl -sS -o "${TMP_FILE}" -w "%{http_code}" \
  -H "Accept: application/json" \
  -H "X-Internal-Token: ${TOKEN}" \
  "${BASE_URL}/admin/fiscal/global/fg1/stub-wave-readiness")"

if [[ "${HTTP_CODE}" != "200" ]]; then
  echo "ERROR: endpoint retornou HTTP ${HTTP_CODE}" >&2
  cat "${TMP_FILE}" >&2
  rm -f "${TMP_FILE}"
  exit 3
fi

python3 - "${TMP_FILE}" "${AS_JSON}" "${JSON_PATH}" <<'PY'
import json
import pathlib
import shutil
import sys
from datetime import datetime, timezone

path = pathlib.Path(sys.argv[1])
as_json = sys.argv[2] == "1"
json_path_arg = str(sys.argv[3] or "").strip()
payload = json.loads(path.read_text(encoding="utf-8"))

decision = str(payload.get("decision") or "").upper()
checks = payload.get("checks") or []
failed = [check for check in checks if str(check.get("status") or "").upper() != "PASS"]

result = {
    "name": "fg1_stub_wave_readiness_smoke",
    "decision": decision,
    "result": "PASS" if decision == "GO" and not failed else "FAIL",
    "failed_checks": [str(check.get("name") or "-") for check in failed],
    "countries_not_ready": int(payload.get("countries_not_ready") or 0),
    "country_count": int(payload.get("country_count") or 0),
}

if as_json and not json_path_arg:
    print(json.dumps(result, ensure_ascii=False))
else:
    print(f"[FG1-STUB-WAVE-READINESS] decision={result['decision']} result={result['result']}")
    print(f"failed_checks={','.join(result['failed_checks']) if result['failed_checks'] else '-'}")
    print(f"countries_not_ready={result['countries_not_ready']}/{result['country_count']}")

if result["result"] != "PASS":
    exit_code = 4
else:
    exit_code = 0

if as_json and json_path_arg:
    out_path = pathlib.Path(json_path_arg)
    latest_path = out_path.parent / "fg1_stub_wave_readiness_smoke_latest.json"
    output_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        **result,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.copyfile(out_path, latest_path)
    print(f"JSON_EXPORT={out_path}")
    print(f"JSON_LATEST={latest_path}")

sys.exit(exit_code)
PY

rm -f "${TMP_FILE}"
