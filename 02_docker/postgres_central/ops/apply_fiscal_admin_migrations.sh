#!/usr/bin/env bash
# Migrações fiscal_admin no postgres_central (locker_central).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIG_SRC="$(cd "$SCRIPT_DIR/../../../01_source/fiscal_admin_service/migrations" && pwd)"
CONTAINER="${POSTGRES_CONTAINER:-postgres_central}"
DB="${POSTGRES_DB:-locker_central}"
USER="${POSTGRES_USER:-admin}"

for f in 001_fiscal_admin.sql 002_fiscal_global_ops.sql; do
  echo "Applying $f ..."
  docker exec -i "$CONTAINER" psql -U "$USER" -d "$DB" < "$MIG_SRC/$f"
done
echo "fiscal_admin migrations applied."
