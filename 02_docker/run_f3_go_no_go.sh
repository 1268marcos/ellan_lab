#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8020}"
TOKEN="${INTERNAL_TOKEN:-}"

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
  echo "ERROR: INTERNAL_TOKEN não definido e não foi possível ler do container billing_fiscal_service." >&2
  exit 1
fi

echo "== F-3 BR/PT GO-NO-GO =="
echo "BASE_URL=${BASE_URL}"
echo

echo "[BR]"
curl -s "${BASE_URL}/admin/fiscal/providers/br-go-no-go?run_connectivity=true" \
  -H "X-Internal-Token: ${TOKEN}"
echo
echo
echo "[PT]"
curl -s "${BASE_URL}/admin/fiscal/providers/pt-go-no-go?run_connectivity=true" \
  -H "X-Internal-Token: ${TOKEN}"
echo
