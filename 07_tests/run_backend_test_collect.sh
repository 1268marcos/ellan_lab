#!/usr/bin/env bash
# Agrega pytest --collect-only nos três backends Python do lab.
# Uso: a partir da raiz do repositório: ./07_tests/run_backend_test_collect.sh
# Ou: make test-collect
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

die() {
  echo "" >&2
  echo "ERRO: $*" >&2
  exit 1
}

gateway_venv_help() {
  cat >&2 <<'EOF'

Para o payment_gateway, crie um venv local dedicado (não reutilize .venv de outro serviço):

  cd 01_source/payment_gateway
  python3 -m venv .venv
  .venv/bin/pip install -U pip
  .venv/bin/pip install -r requirements.txt

Depois reexecute: make test-collect   ou   ./07_tests/run_backend_test_collect.sh

CI: o workflow .github/workflows/backend-test-collect.yml instala dependências em .venv
em cada um dos três serviços antes de correr este script.
EOF
}

run_collect() {
  local label="$1"
  local dir="$2"
  local venv_subdir="$3"
  local pytest_args="$4"

  local pytest_bin="${dir}/${venv_subdir}/bin/pytest"
  if [[ ! -x "${pytest_bin}" ]]; then
    if [[ "${label}" == "payment_gateway" ]]; then
      echo "ERRO [${label}]: ${pytest_bin} não existe ou não é executável." >&2
      gateway_venv_help
      exit 1
    fi
    die "[${label}] pytest não encontrado em ${pytest_bin}. Crie o venv em ${dir} e instale requirements.txt."
  fi

  echo ""
  echo "== ${label}: pytest --collect-only ${pytest_args} =="
  (
    cd "${dir}"
    PYTHONPATH=. "${pytest_bin}" ${pytest_args} --collect-only -q
  )
}

echo "== Backend test collect (raiz: ${ROOT_DIR}) =="

run_collect "billing_fiscal_service" "${ROOT_DIR}/01_source/backend/billing_fiscal_service" ".venv" "tests/"
run_collect "order_pickup_service" "${ROOT_DIR}/01_source/order_pickup_service" ".venv" "tests/"
run_collect "payment_gateway" "${ROOT_DIR}/01_source/payment_gateway" ".venv" "app/integrations/tests/"

echo ""
echo "OK: collect-only concluído nos três backends."
