#!/bin/bash
set -e

echo "=== Frontend Build ==="
(cd 01_source/frontend && npm run build)

echo "=== Fiscal Smoke ==="
bash 02_docker/run_fiscal_routes_smoke.sh

echo "=== Backend Tests ==="
bash 07_tests/run_backend_test_collect.sh
