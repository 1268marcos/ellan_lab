#!/usr/bin/env bash
# Migrações security 009–013 (partner_admin) no postgres_central.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIG_SRC="$(cd "$SCRIPT_DIR/../../../01_source/partner_admin_service/migrations" && pwd)"
CONTAINER="${POSTGRES_CONTAINER:-postgres_central}"
DB="${POSTGRES_DB:-locker_central}"
USER="${POSTGRES_USER:-admin}"

if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "Container $CONTAINER não está rodando." >&2
  exit 1
fi

for f in \
  009_security_domain.sql \
  010_security_professional.sql \
  011_security_locker_players.sql \
  012_security_ecosystem_taxonomy.sql \
  013_security_value_layer.sql \
  014_security_cross_domain_ops.sql; do
  path="$MIG_SRC/$f"
  [[ -f "$path" ]] || { echo "Ausente: $path" >&2; exit 1; }
  echo "Applying $f ..."
  docker exec -i "$CONTAINER" psql -v ON_ERROR_STOP=1 -U "$USER" -d "$DB" < "$path"
done

echo "partner_admin security migrations applied."
docker exec "$CONTAINER" psql -U "$USER" -d "$DB" -c \
  "SELECT tablename FROM pg_tables WHERE tablename LIKE 'security_%' ORDER BY 1;"
