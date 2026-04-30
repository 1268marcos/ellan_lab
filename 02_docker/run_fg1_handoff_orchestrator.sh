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

echo "== FG1 HANDOFF ORCHESTRATOR =="
echo "ENV_FILE=${ENV_FILE}"
echo "FISCAL_BASE_URL=${FISCAL_BASE_URL}"
echo

WORK_DIR="/tmp/fg1_handoff_orchestrator_${TIMESTAMP_UTC}"
mkdir -p "${WORK_DIR}"

SMOKE_FIXTURE="/home/marcos/ellan_lab/02_docker/run_fg1_fixture_inventory_smoke.sh"
SMOKE_ENVELOPE="/home/marcos/ellan_lab/02_docker/run_fg1_envelope_check_smoke.sh"
SMOKE_TRACE="/home/marcos/ellan_lab/02_docker/run_fg1_simulate_trace_smoke.sh"
SMOKE_WAVE_READINESS="/home/marcos/ellan_lab/02_docker/run_fg1_stub_wave_readiness_smoke.sh"

run_smoke() {
  local label="$1"
  local script_path="$2"
  local out_json="$3"
  local exit_file="$4"
  if "${script_path}" --json --json-path "${out_json}" --env-file "${ENV_FILE}" >/tmp/"${label}".log 2>&1; then
    echo 0 >"${exit_file}"
    echo "[OK] ${label}"
  else
    code=$?
    echo "${code}" >"${exit_file}"
    echo "[ERRO] ${label} (exit=${code})"
  fi
}

run_smoke "fg1_fixture_inventory_smoke" "${SMOKE_FIXTURE}" "${WORK_DIR}/fixture_inventory.json" "${WORK_DIR}/fixture_inventory.exit"
run_smoke "fg1_envelope_check_smoke" "${SMOKE_ENVELOPE}" "${WORK_DIR}/envelope_check.json" "${WORK_DIR}/envelope_check.exit"
run_smoke "fg1_simulate_trace_smoke" "${SMOKE_TRACE}" "${WORK_DIR}/simulate_trace.json" "${WORK_DIR}/simulate_trace.exit"
run_smoke "fg1_stub_wave_readiness_smoke" "${SMOKE_WAVE_READINESS}" "${WORK_DIR}/stub_wave_readiness.json" "${WORK_DIR}/stub_wave_readiness.exit"

python3 - "${WORK_DIR}" "${LOG_DIR}" "${JSON_ENABLED}" "${JSON_PATH}" "${FISCAL_BASE_URL}" "${ENV_FILE}" <<'PY'
import json
import pathlib
import shutil
import sys
from datetime import datetime, timezone

work_dir = pathlib.Path(sys.argv[1])
log_dir = pathlib.Path(sys.argv[2])
json_enabled = sys.argv[3].lower() == "true"
json_path_arg = sys.argv[4]
fiscal_base_url = sys.argv[5]
env_file = sys.argv[6]

def read_json(path: pathlib.Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

def read_exit(path: pathlib.Path) -> int:
    if not path.exists():
        return 99
    try:
        return int(path.read_text(encoding="utf-8").strip() or "99")
    except Exception:
        return 99

fixture = read_json(work_dir / "fixture_inventory.json")
envelope = read_json(work_dir / "envelope_check.json")
trace = read_json(work_dir / "simulate_trace.json")
wave_readiness = read_json(work_dir / "stub_wave_readiness.json")

checks = [
    {
        "name": "fixture_inventory",
        "exit_code": read_exit(work_dir / "fixture_inventory.exit"),
        "result": fixture.get("result") or fixture.get("summary", {}).get("result"),
        "fail_count": fixture.get("fail_count"),
    },
    {
        "name": "envelope_check",
        "exit_code": read_exit(work_dir / "envelope_check.exit"),
        "result": envelope.get("result") or envelope.get("summary", {}).get("result"),
        "fail_count": envelope.get("fail_count"),
    },
    {
        "name": "simulate_trace",
        "exit_code": read_exit(work_dir / "simulate_trace.exit"),
        "result": trace.get("result") or trace.get("summary", {}).get("result"),
        "fail_count": trace.get("fail_count") if "fail_count" in trace else trace.get("summary", {}).get("fail_count"),
    },
    {
        "name": "stub_wave_readiness",
        "exit_code": read_exit(work_dir / "stub_wave_readiness.exit"),
        "result": wave_readiness.get("result") or wave_readiness.get("summary", {}).get("result"),
        "fail_count": wave_readiness.get("fail_count") if "fail_count" in wave_readiness else wave_readiness.get("summary", {}).get("fail_count"),
    },
]

errors = [c for c in checks if c["exit_code"] != 0]
decision = "GO" if len(errors) == 0 else "NO_GO"
result = "FG1_HANDOFF_ORCHESTRATOR_OK" if decision == "GO" else "FG1_HANDOFF_ORCHESTRATOR_FAIL"

payload = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "result": result,
    "decision": decision,
    "fiscal_base_url": fiscal_base_url,
    "env_file": env_file,
    "checks": checks,
    "fixture_inventory": fixture,
    "envelope_check": envelope,
    "simulate_trace": trace,
    "stub_wave_readiness": wave_readiness,
}

print(json.dumps({"summary": {"result": result, "decision": decision, "errors": len(errors)}}, ensure_ascii=False))

if json_enabled:
    log_dir.mkdir(parents=True, exist_ok=True)
    if json_path_arg:
        json_path = pathlib.Path(json_path_arg)
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        json_path = log_dir / f"fg1_handoff_orchestrator_{ts}.json"
    latest_path = log_dir / "fg1_handoff_orchestrator_latest.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.copyfile(json_path, latest_path)
    print(f"JSON_EXPORT={json_path}")
    print(f"JSON_LATEST={latest_path}")

if decision != "GO":
    sys.exit(2)
PY

echo
echo "RESULTADO FINAL: FG1_HANDOFF_ORCHESTRATOR_OK"
