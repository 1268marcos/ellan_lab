#!/usr/bin/env bash
# Testes de contrato leves: pagamento → runtime (HTTP) e pickup → lifecycle (HTTP) + hook interno.
# Sem Docker; usa os .venv de cada serviço.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

run_pickup() {
  local d="${ROOT_DIR}/01_source/order_pickup_service"
  local py="${d}/.venv/bin/python"
  [[ -x "${py}" ]] || {
    echo "ERRO: ${py} não encontrado." >&2
    exit 1
  }
  (
    cd "${d}"
    PYTHONPATH=. "${py}" -m pytest \
      tests/test_lifecycle_client_prepayment_cancel.py \
      tests/test_internal_prepayment_cancel_on_payment_path.py \
      -q
  )
}

run_gateway() {
  local d="${ROOT_DIR}/01_source/payment_gateway"
  local py="${d}/.venv/bin/python"
  [[ -x "${py}" ]] || {
    echo "ERRO: payment_gateway sem .venv. Crie com: cd ${d} && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt" >&2
    exit 1
  }
  (
    cd "${d}"
    PYTHONPATH=. "${py}" -m pytest \
      app/integrations/tests/test_locker_backend_runtime.py \
      -q
  )
}

echo "== payment-runtime contract tests =="
run_pickup
run_gateway
echo "OK."
