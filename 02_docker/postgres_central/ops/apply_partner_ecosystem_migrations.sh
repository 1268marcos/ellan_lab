#!/usr/bin/env bash
# Aplica migrações 004–006 (partner ecossistema + webhooks) no postgres_central.
#
# Uso:
#   cd 02_docker/postgres_central/ops
#   ./apply_partner_ecosystem_migrations.sh
#
# Variáveis:
#   POSTGRES_CONTAINER=postgres_central
#   POSTGRES_USER=admin
#   POSTGRES_DB=locker_central

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIG_DIR="$(cd "$SCRIPT_DIR/../migrations" && pwd)"
CONTAINER="${POSTGRES_CONTAINER:-postgres_central}"
DB_USER="${POSTGRES_USER:-admin}"
DB_NAME="${POSTGRES_DB:-locker_central}"

if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "Container $CONTAINER não está rodando. Suba com: cd 02_docker && docker compose up -d postgres_central" >&2
  exit 1
fi

for f in 004_partner_ecosystem.sql 005_partner_ecosystem_professional.sql 006_partner_capability_webhooks.sql \
  007_partner_global_ops.sql 008_partner_webhook_dlq_corridor_sla_cert_mirror.sql; do
  path="$MIG_DIR/$f"
  if [[ ! -f "$path" ]]; then
    echo "Arquivo ausente: $path" >&2
    exit 1
  fi
  echo "Applying $f ..."
  docker exec -i "$CONTAINER" psql -v ON_ERROR_STOP=1 -U "$DB_USER" -d "$DB_NAME" < "$path"
done

echo "Done. Verifique:"
docker exec "$CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c \
  "SELECT tablename FROM pg_tables WHERE tablename LIKE 'partner_%' ORDER BY 1;"
