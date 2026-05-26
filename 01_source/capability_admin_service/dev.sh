#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi
export PYTHONPATH=.
exec .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "${CAPABILITY_ADMIN_PORT:-8028}" --reload
