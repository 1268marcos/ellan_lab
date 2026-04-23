#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/01_source/order_pickup_service"
FRONTEND_DIR="${ROOT_DIR}/01_source/frontend"

PYTHON_BIN="${PYTHON_BIN:-${BACKEND_DIR}/.venv_test/bin/python}"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Erro: python de teste não encontrado em ${PYTHON_BIN}" >&2
  exit 1
fi

echo "== Sprint 5 / Item 5 - Smoke gate =="

cd "${BACKEND_DIR}"

echo ""
echo "[1/3] Backend: bloqueios OPS sem side effects"
"${PYTHON_BIN}" -m pytest tests/test_ops_incident_safe_sprint5.py -q

echo ""
echo "[2/3] Backend: matriz de roles (guard básico)"
"${PYTHON_BIN}" -m pytest tests/test_user_roles_sprint3.py -q

cd "${FRONTEND_DIR}"

echo ""
echo "[3/3] Frontend: guard de rotas /ops/*"
npm test -- --run

echo ""
echo "OK: Smoke Sprint 5 / Item 5 concluído com sucesso."
