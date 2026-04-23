#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/01_source/order_pickup_service"
FRONTEND_DIR="${ROOT_DIR}/01_source/frontend"

PYTHON_BIN="${PYTHON_BIN:-${BACKEND_DIR}/.venv_test/bin/python}"
ORDER_PICKUP_TEST_DATABASE_URL="${ORDER_PICKUP_TEST_DATABASE_URL:-postgresql+psycopg://admin:admin123@localhost:5435/locker_central}"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Erro: python de teste não encontrado em ${PYTHON_BIN}" >&2
  exit 1
fi

echo "== Sprint 5 / Item 5 - Regressão incident-safe =="
echo "ORDER_PICKUP_TEST_DATABASE_URL=${ORDER_PICKUP_TEST_DATABASE_URL}"

cd "${BACKEND_DIR}"
export ORDER_PICKUP_TEST_DATABASE_URL

echo ""
echo "[1/5] Backend: bloqueios OPS sem side effects"
"${PYTHON_BIN}" -m pytest tests/test_ops_incident_safe_sprint5.py -v

echo ""
echo "[2/5] Backend: recuperação + idempotência (Postgres)"
"${PYTHON_BIN}" -m pytest tests/test_public_order_cancel_compensation.py -v

echo ""
echo "[3/5] Backend: matriz de roles sprint 3"
"${PYTHON_BIN}" -m pytest tests/test_user_roles_sprint3.py -v

cd "${FRONTEND_DIR}"

echo ""
echo "[4/5] Frontend: guard de rotas /ops/*"
npm test

echo ""
echo "[5/5] Frontend: build de segurança"
npm run build

echo ""
echo "OK: Regressão Sprint 5 / Item 5 concluída com sucesso."
