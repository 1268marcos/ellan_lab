#!/usr/bin/env bash
# P3 — Playwright no checkout público (smoke sem backend; fluxo DEV opcional com token).
# Pré-requisito: Node 20+; na primeira vez instala browsers: npx playwright install chromium
#
# Variáveis:
#   PLAYWRIGHT_START_VITE — "1" (default) arranca Vite; "0" se já corre em FRONTEND_BASE_URL
#   FRONTEND_BASE_URL     — default http://127.0.0.1:5173
#   E2E_PUBLIC_AUTH_TOKEN — opcional; ativa teste checkout-dev-full (utilizador + stack reais)
#   E2E_CHECKOUT_LOCKER_ID / E2E_CHECKOUT_SKU_ID / E2E_CHECKOUT_SLOT — opcional para o fluxo DEV
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}/01_source/frontend"

npm ci
npx playwright install chromium

export PLAYWRIGHT_START_VITE="${PLAYWRIGHT_START_VITE:-1}"
export FRONTEND_BASE_URL="${FRONTEND_BASE_URL:-http://127.0.0.1:5173}"

exec npx playwright test "$@"
