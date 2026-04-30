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

echo "== FG1 SIMULATE TRACE SMOKE =="
echo "ENV_FILE=${ENV_FILE}"
echo "FISCAL_BASE_URL=${FISCAL_BASE_URL}"
echo

FAIL_COUNT=0
REASON="ok"
RESULTS_FILE="/tmp/fg1_simulate_trace_smoke_results.json"

python3 - "${FISCAL_BASE_URL}" "${INTERNAL_TOKEN}" "${RESULTS_FILE}" <<'PY'
import json
import sys
import urllib.parse
import urllib.request

base = sys.argv[1].rstrip("/")
token = sys.argv[2]
out = sys.argv[3]

cases = [
    {"country": "US", "operation": "authorize", "scenario": "AUTHORIZE_SUCCESS", "region": "US-CA"},
    {"country": "CA", "operation": "correct", "scenario": "CORRECT_SUCCESS", "region": "CA-QC"},
    {"country": "PL", "operation": "cancel", "scenario": "CANCEL_DEADLINE_EXPIRED"},
    {"country": "FR", "operation": "status", "scenario": "STATUS_NOT_FOUND"},
]

results = []
fail_count = 0

for case in cases:
    params = urllib.parse.urlencode(case)
    url = f"{base}/admin/fiscal/global/fg1/simulate?{params}"
    req = urllib.request.Request(url, method="POST")
    req.add_header("X-Internal-Token", token)
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            code = int(resp.getcode())
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        results.append({"case": case, "ok": False, "error": str(exc)})
        fail_count += 1
        continue

    telemetry = payload.get("telemetry") or {}
    gov_raw = (payload.get("government_response") or {}).get("raw") or {}
    required_telemetry = ["trace_id", "provider_adapter", "region", "fixture_source", "event_name", "timestamp"]
    required_raw = ["trace_id", "provider_adapter", "region", "scenario", "operation", "country_code"]
    missing_telemetry = [k for k in required_telemetry if not telemetry.get(k)]
    missing_raw = [k for k in required_raw if not gov_raw.get(k)]
    cross_fail = []
    if telemetry.get("trace_id") != gov_raw.get("trace_id"):
        cross_fail.append("trace_id_mismatch")
    if telemetry.get("provider_adapter") != gov_raw.get("provider_adapter"):
        cross_fail.append("provider_adapter_mismatch")
    if telemetry.get("region") != gov_raw.get("region"):
        cross_fail.append("region_mismatch")
    ok = code == 200 and not missing_telemetry and not missing_raw and not cross_fail
    if not ok:
        fail_count += 1
    results.append(
        {
            "case": case,
            "ok": ok,
            "http_code": code,
            "missing_telemetry": missing_telemetry,
            "missing_government_raw": missing_raw,
            "cross_checks": cross_fail,
            "trace_id": telemetry.get("trace_id"),
            "provider_adapter": telemetry.get("provider_adapter"),
            "region": telemetry.get("region"),
            "fixture_source": telemetry.get("fixture_source"),
        }
    )

summary = {
    "result": "FG1_SIMULATE_TRACE_SMOKE_OK" if fail_count == 0 else "FG1_SIMULATE_TRACE_SMOKE_FAIL",
    "fail_count": fail_count,
    "cases": len(cases),
}
with open(out, "w", encoding="utf-8") as f:
    json.dump({"summary": summary, "results": results}, f, ensure_ascii=False, indent=2)
print(json.dumps(summary, ensure_ascii=False))
PY

SUMMARY_RESULT="$(python3 - "${RESULTS_FILE}" <<'PY'
import json, sys
data = json.load(open(sys.argv[1], "r", encoding="utf-8"))
print(data["summary"]["result"])
print(data["summary"]["fail_count"])
PY
)"
FINAL_RESULT="$(echo "${SUMMARY_RESULT}" | sed -n '1p')"
FAIL_COUNT="$(echo "${SUMMARY_RESULT}" | sed -n '2p')"
if [[ "${FAIL_COUNT}" != "0" ]]; then
  REASON="simulate_trace_fields_invalid"
fi

if [[ "${JSON_ENABLED}" == "true" ]]; then
  mkdir -p "${LOG_DIR}"
  if [[ -z "${JSON_PATH}" ]]; then
    JSON_PATH="${LOG_DIR}/fg1_simulate_trace_smoke_${TIMESTAMP_UTC}.json"
  fi
  python3 - "${RESULTS_FILE}" "${JSON_PATH}" "${LOG_DIR}/fg1_simulate_trace_smoke_latest.json" "${FINAL_RESULT}" "${FAIL_COUNT}" "${REASON}" "${FISCAL_BASE_URL}" "${ENV_FILE}" <<'PY'
import json
import pathlib
import shutil
import sys
from datetime import datetime, timezone

raw_path = pathlib.Path(sys.argv[1])
json_path = pathlib.Path(sys.argv[2])
latest_path = pathlib.Path(sys.argv[3])
final_result = sys.argv[4]
fail_count = int(sys.argv[5])
reason = sys.argv[6]
fiscal_base_url = sys.argv[7]
env_file = sys.argv[8]
raw = json.loads(raw_path.read_text(encoding="utf-8"))

payload = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "result": final_result,
    "fail_count": fail_count,
    "reason": reason,
    "fiscal_base_url": fiscal_base_url,
    "env_file": env_file,
    **raw,
}
json_path.parent.mkdir(parents=True, exist_ok=True)
json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
shutil.copyfile(json_path, latest_path)
print(f"JSON_EXPORT={json_path}")
print(f"JSON_LATEST={latest_path}")
PY
fi

echo
if [[ "${FAIL_COUNT}" == "0" ]]; then
  echo "RESULTADO FINAL: FG1_SIMULATE_TRACE_SMOKE_OK"
  exit 0
fi
echo "RESULTADO FINAL: FG1_SIMULATE_TRACE_SMOKE_FAIL (${REASON})"
exit 2
