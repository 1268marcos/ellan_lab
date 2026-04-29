#!/usr/bin/env bash
set -euo pipefail

FISCAL_BASE_URL="${FISCAL_BASE_URL:-http://localhost:8020}"
DEFAULT_ENV_FILE="/home/marcos/ellan_lab/02_docker/.env"
LOG_DIR="/home/marcos/ellan_lab/04_logs/ops"
TIMESTAMP_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
ENV_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
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

mkdir -p "${LOG_DIR}"
TMP_COVERAGE="/tmp/fg1_handoff_coverage.json"
TMP_READINESS="/tmp/fg1_handoff_readiness.json"
TMP_ACTION_PLAN="/tmp/fg1_handoff_action_plan.json"

curl -sS "${FISCAL_BASE_URL}/admin/fiscal/global/fg1/coverage-gate" -H "X-Internal-Token: ${INTERNAL_TOKEN}" -H "Accept: application/json" > "${TMP_COVERAGE}"
curl -sS "${FISCAL_BASE_URL}/admin/fiscal/global/fg1/readiness-gate" -H "X-Internal-Token: ${INTERNAL_TOKEN}" -H "Accept: application/json" > "${TMP_READINESS}"
curl -sS "${FISCAL_BASE_URL}/admin/fiscal/global/fg1/readiness-action-plan" -H "X-Internal-Token: ${INTERNAL_TOKEN}" -H "Accept: application/json" > "${TMP_ACTION_PLAN}"

JSON_TS_PATH="${LOG_DIR}/fg1_final_decision_${TIMESTAMP_UTC}.json"
JSON_LATEST_PATH="${LOG_DIR}/fg1_final_decision_latest.json"

python3 - "${TMP_COVERAGE}" "${TMP_READINESS}" "${TMP_ACTION_PLAN}" "${JSON_TS_PATH}" "${JSON_LATEST_PATH}" <<'PY'
import json
import pathlib
import shutil
import sys
from datetime import datetime, timezone

coverage_path = pathlib.Path(sys.argv[1])
readiness_path = pathlib.Path(sys.argv[2])
action_plan_path = pathlib.Path(sys.argv[3])
json_ts_path = pathlib.Path(sys.argv[4])
json_latest_path = pathlib.Path(sys.argv[5])

coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
action_plan = json.loads(action_plan_path.read_text(encoding="utf-8"))

coverage_map = {str(i.get("country_code")).upper(): str(i.get("coverage_status", "NO_GO")).upper() for i in coverage.get("countries", [])}
readiness_map = {str(i.get("country_code")).upper(): str(i.get("readiness_status", "NO_GO")).upper() for i in readiness.get("countries", [])}
plan_map = {str(i.get("country_code")).upper(): int(i.get("blocking_reasons_count", 0)) for i in action_plan.get("items", [])}

countries = sorted(set([*coverage_map.keys(), *readiness_map.keys(), *plan_map.keys()]))
rows = []
for country in countries:
    coverage_status = coverage_map.get(country, "NO_GO")
    readiness_status = readiness_map.get(country, "NO_GO")
    pending_actions = plan_map.get(country, 0)
    final_decision = "GO" if (coverage_status == "GO" and readiness_status == "GO" and pending_actions == 0) else "NO_GO"
    rows.append(
        {
            "country_code": country,
            "coverage_status": coverage_status,
            "readiness_status": readiness_status,
            "pending_actions": pending_actions,
            "final_decision": final_decision,
        }
    )

final_global_decision = "GO" if rows and all(r["final_decision"] == "GO" for r in rows) else "NO_GO"
payload = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "scope": "FG-1-FINAL-DECISION",
    "final_global_decision": final_global_decision,
    "countries_ready": sum(1 for r in rows if r["final_decision"] == "GO"),
    "countries_blocked": sum(1 for r in rows if r["final_decision"] != "GO"),
    "country_count": len(rows),
    "sources": {
        "coverage_gate_version": coverage.get("gate_version"),
        "readiness_gate_version": readiness.get("gate_version"),
        "action_plan_version": action_plan.get("plan_version"),
    },
    "countries": rows,
}

json_ts_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
shutil.copyfile(json_ts_path, json_latest_path)
print(f"JSON_EXPORT={json_ts_path}")
print(f"JSON_LATEST={json_latest_path}")
print(f"FINAL_DECISION={final_global_decision}")
PY

