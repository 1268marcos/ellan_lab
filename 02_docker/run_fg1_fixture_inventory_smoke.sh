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

echo "== FG1 FIXTURE INVENTORY SMOKE =="
echo "ENV_FILE=${ENV_FILE}"
echo "FISCAL_BASE_URL=${FISCAL_BASE_URL}"
echo

INV="/tmp/fg1_fixture_inventory_smoke.json"
DOC="/tmp/fg1_fixture_document_smoke.json"

HTTP_INV="$(curl -sS -o "${INV}" -w "%{http_code}" "${FISCAL_BASE_URL}/admin/fiscal/global/fg1/fixture-inventory" -H "X-Internal-Token: ${INTERNAL_TOKEN}" -H "Accept: application/json")"
HTTP_DOC="$(curl -sS -G -o "${DOC}" -w "%{http_code}" "${FISCAL_BASE_URL}/admin/fiscal/global/fg1/fixture-document" \
  --data-urlencode "country=US" \
  --data-urlencode "operation=authorize" \
  --data-urlencode "scenario=AUTHORIZE_SUCCESS" \
  -H "X-Internal-Token: ${INTERNAL_TOKEN}" -H "Accept: application/json")"

FAIL_COUNT=0
FINAL_RESULT="FG1_FIXTURE_INVENTORY_SMOKE_OK"
REASON="ok"

if [[ "${HTTP_INV}" != "200" ]]; then
  FAIL_COUNT=$((FAIL_COUNT + 1))
  FINAL_RESULT="FG1_FIXTURE_INVENTORY_SMOKE_FAIL"
  REASON="inventory_http_${HTTP_INV}"
elif [[ "${HTTP_DOC}" != "200" ]]; then
  FAIL_COUNT=$((FAIL_COUNT + 1))
  FINAL_RESULT="FG1_FIXTURE_INVENTORY_SMOKE_FAIL"
  REASON="document_http_${HTTP_DOC}"
else
  if ! python3 - "${INV}" <<'PY'
import json, pathlib, sys
p = pathlib.Path(sys.argv[1])
d = json.loads(p.read_text(encoding="utf-8"))
assert d.get("complete") is True, "fixture inventory not complete"
assert d.get("count") == d.get("expected_count"), "fixture count mismatch"
PY
  then
    FAIL_COUNT=$((FAIL_COUNT + 1))
    FINAL_RESULT="FG1_FIXTURE_INVENTORY_SMOKE_FAIL"
    REASON="inventory_not_complete"
  fi
fi

python3 - "${INV}" "${DOC}" "${HTTP_INV}" "${HTTP_DOC}" "${FINAL_RESULT}" "${REASON}" <<'PY'
import json
import pathlib
import sys

inv_path = pathlib.Path(sys.argv[1])
doc_path = pathlib.Path(sys.argv[2])
http_inv = int(sys.argv[3])
http_doc = int(sys.argv[4])
final = sys.argv[5]
reason = sys.argv[6]

def load(p):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}

inv = load(inv_path)
doc = load(doc_path)
summary = {
    "http_inventory": http_inv,
    "http_document": http_doc,
    "result": final,
    "reason": reason,
    "inventory_complete": inv.get("complete"),
    "inventory_count": inv.get("count"),
    "expected_count": inv.get("expected_count"),
    "document_authority": doc.get("authority"),
    "document_scenario": doc.get("scenario"),
}
print(json.dumps({"summary": summary}, ensure_ascii=False))
PY

if [[ "${JSON_ENABLED}" == "true" ]]; then
  mkdir -p "${LOG_DIR}"
  if [[ -z "${JSON_PATH}" ]]; then
    JSON_PATH="${LOG_DIR}/fg1_fixture_inventory_smoke_${TIMESTAMP_UTC}.json"
  fi
  python3 - "${INV}" "${DOC}" "${JSON_PATH}" "${LOG_DIR}/fg1_fixture_inventory_smoke_latest.json" "${FINAL_RESULT}" "${FAIL_COUNT}" "${REASON}" "${HTTP_INV}" "${HTTP_DOC}" "${FISCAL_BASE_URL}" "${ENV_FILE}" <<'PY'
import json
import pathlib
import shutil
import sys
from datetime import datetime, timezone

inv_path = pathlib.Path(sys.argv[1])
doc_path = pathlib.Path(sys.argv[2])
json_path = pathlib.Path(sys.argv[3])
latest_path = pathlib.Path(sys.argv[4])
final_result = sys.argv[5]
fail_count = int(sys.argv[6])
reason = sys.argv[7]
http_inv = int(sys.argv[8])
http_doc = int(sys.argv[9])
fiscal_base_url = sys.argv[10]
env_file = sys.argv[11]

def load(p):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}

payload = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "result": final_result,
    "fail_count": fail_count,
    "reason": reason,
    "http_inventory": http_inv,
    "http_document": http_doc,
    "fiscal_base_url": fiscal_base_url,
    "env_file": env_file,
    "inventory": load(inv_path),
    "document_sample": load(doc_path),
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
  echo "RESULTADO FINAL: FG1_FIXTURE_INVENTORY_SMOKE_OK"
  exit 0
fi
echo "RESULTADO FINAL: FG1_FIXTURE_INVENTORY_SMOKE_FAIL (${REASON})"
exit 2
