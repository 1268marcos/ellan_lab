#!/usr/bin/env bash
# Migrações marketplace_admin no postgres_central (locker_central).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIG_SRC="$(cd "$SCRIPT_DIR/../../../01_source/marketplace_admin_service/migrations" && pwd)"
MIG_CENTRAL="$(cd "$SCRIPT_DIR/../migrations" && pwd)"
CONTAINER="${POSTGRES_CONTAINER:-postgres_central}"
DB_USER="${POSTGRES_USER:-admin}"
DB_NAME="${POSTGRES_DB:-locker_central}"

if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "Container $CONTAINER não está rodando." >&2
  exit 1
fi

for f in 001_marketplace_admin.sql 002_marketplace_professional.sql 003_marketplace_channel_players.sql \
  004_channel_integration_meta.sql 005_integration_readiness.sql 006_readiness_alerts_capability_webhooks.sql \
  007_marketplace_global_ops.sql 008_marketplace_webhook_dlq_corridor_sla_cert_mirror.sql; do
  path="$MIG_SRC/$f"
  if [[ ! -f "$path" ]]; then
    path="$MIG_CENTRAL/$f"
  fi
  if [[ ! -f "$path" ]]; then
    echo "Arquivo ausente: $f" >&2
    exit 1
  fi
  echo "Applying $f ..."
  docker exec -i "$CONTAINER" psql -v ON_ERROR_STOP=1 -U "$DB_USER" -d "$DB_NAME" < "$path"
done

echo "marketplace_global_corridors:"
docker exec "$CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c \
  "SELECT COUNT(*) AS n FROM marketplace_global_corridors;" 2>/dev/null || true
