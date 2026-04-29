#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-}"
BASE_URL="${BASE_URL:-http://localhost:8020}"
TOKEN="${INTERNAL_TOKEN:-}"

read_from_env_file() {
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

if [[ -n "${ENV_FILE}" && -f "${ENV_FILE}" ]]; then
  if [[ -z "${TOKEN}" ]]; then
    TOKEN="$(read_from_env_file "ORDER_INTERNAL_TOKEN" "${ENV_FILE}")"
  fi
  BR_ENABLED="$(read_from_env_file "FISCAL_REAL_PROVIDER_BR_ENABLED" "${ENV_FILE}")"
  PT_ENABLED="$(read_from_env_file "FISCAL_REAL_PROVIDER_PT_ENABLED" "${ENV_FILE}")"
  BR_BASE_URL="$(read_from_env_file "FISCAL_REAL_PROVIDER_BASE_URL_BR" "${ENV_FILE}")"
  PT_BASE_URL="$(read_from_env_file "FISCAL_REAL_PROVIDER_BASE_URL_PT" "${ENV_FILE}")"
  BR_API_KEY="$(read_from_env_file "FISCAL_REAL_PROVIDER_API_KEY_BR" "${ENV_FILE}")"
  PT_API_KEY="$(read_from_env_file "FISCAL_REAL_PROVIDER_API_KEY_PT" "${ENV_FILE}")"
else
  BR_ENABLED="${FISCAL_REAL_PROVIDER_BR_ENABLED:-}"
  PT_ENABLED="${FISCAL_REAL_PROVIDER_PT_ENABLED:-}"
  BR_BASE_URL="${FISCAL_REAL_PROVIDER_BASE_URL_BR:-}"
  PT_BASE_URL="${FISCAL_REAL_PROVIDER_BASE_URL_PT:-}"
  BR_API_KEY="${FISCAL_REAL_PROVIDER_API_KEY_BR:-}"
  PT_API_KEY="${FISCAL_REAL_PROVIDER_API_KEY_PT:-}"
fi

if [[ -z "${TOKEN}" ]]; then
  has_billing_container="false"
  while IFS= read -r name; do
    if [[ "${name}" == "billing_fiscal_service" ]]; then
      has_billing_container="true"
      break
    fi
  done < <(docker ps --format '{{.Names}}')
  if [[ "${has_billing_container}" == "true" ]]; then
    TOKEN="$(docker exec billing_fiscal_service /bin/sh -lc 'printf %s "$INTERNAL_TOKEN"')"
  fi
fi

if [[ -z "${TOKEN}" ]]; then
  echo "ERROR: INTERNAL_TOKEN ausente (env/arquivo/container)." >&2
  exit 1
fi

echo "== F-3 PREFLIGHT =="
echo "BASE_URL=${BASE_URL}"
echo "ENV_FILE=${ENV_FILE:-<none>}"
echo

missing=0
check_required() {
  local label="$1"
  local val="$2"
  if [[ -z "${val}" ]]; then
    echo "[PENDENTE] ${label}"
    missing=$((missing + 1))
  else
    echo "[OK] ${label}"
  fi
}

if [[ "${BR_ENABLED,,}" == "true" ]]; then
  check_required "BR BASE URL" "${BR_BASE_URL}"
  check_required "BR API KEY" "${BR_API_KEY}"
fi
if [[ "${PT_ENABLED,,}" == "true" ]]; then
  check_required "PT BASE URL" "${PT_BASE_URL}"
  check_required "PT API KEY" "${PT_API_KEY}"
fi
if [[ "${BR_ENABLED,,}" != "true" && "${PT_ENABLED,,}" != "true" ]]; then
  echo "[INFO] BR/PT real desabilitados no env analisado."
fi
echo

BR_JSON="$(curl -s "${BASE_URL}/admin/fiscal/providers/br-go-no-go?run_connectivity=true" -H "X-Internal-Token: ${TOKEN}")"
PT_JSON="$(curl -s "${BASE_URL}/admin/fiscal/providers/pt-go-no-go?run_connectivity=true" -H "X-Internal-Token: ${TOKEN}")"

python3 - "$BR_JSON" "$PT_JSON" <<'PY'
import json, sys
br = json.loads(sys.argv[1])
pt = json.loads(sys.argv[2])
print("[BR]", br.get("go_no_go"), "-", br.get("summary"))
print("[PT]", pt.get("go_no_go"), "-", pt.get("summary"))
PY

BR_GO="$(python3 - "$BR_JSON" <<'PY'
import json, sys
print(json.loads(sys.argv[1]).get("go_no_go", "NO_GO"))
PY
)"
PT_GO="$(python3 - "$PT_JSON" <<'PY'
import json, sys
print(json.loads(sys.argv[1]).get("go_no_go", "NO_GO"))
PY
)"

echo
if [[ ${missing} -eq 0 && "${BR_GO}" == "GO" && "${PT_GO}" == "GO" ]]; then
  echo "RESULTADO FINAL: GO"
  exit 0
fi
echo "RESULTADO FINAL: NO_GO"
exit 2
