#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH=.
.venv/bin/python -c "
from app.core.database import init_db
init_db()
print('partner_admin migrations applied (create_all + 009-013 SQL).')
"
