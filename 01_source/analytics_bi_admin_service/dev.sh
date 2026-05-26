#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi
export DATABASE_URL="${DATABASE_URL:-postgresql://admin:admin123@127.0.0.1:5435/locker_central}"
export SEED_ON_START="${SEED_ON_START:-true}"
exec .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "${ANALYTICS_BI_ADMIN_PORT:-8026}" --reload
