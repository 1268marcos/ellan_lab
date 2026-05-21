#!/usr/bin/env bash
# Rebuild controlado do postgres_central (banco locker_central).
#
# Pré-requisitos:
#   - Container postgres_central rodando (docker compose up -d postgres_central)
#   - Volume NOVO ou banco recriado (este script não apaga volume sozinho)
#
# Uso:
#   cd 02_docker/postgres_central/schema_rebuild
#   ./run_rebuild.sh              # todas as fases
#   ./run_rebuild.sh 09_views     # só uma fase (prefixo do arquivo)
#   DESTROY_VOLUME=1 ./run_rebuild.sh   # down -v + remove 03_data (destrutivo)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
CONTAINER="${POSTGRES_CONTAINER:-postgres_central}"
DB_USER="${POSTGRES_USER:-admin}"
DB_NAME="${POSTGRES_DB:-locker_central}"
ONLY_PHASE="${1:-}"
# SKIP_TIMESCALEDB=1 — pula extensão/hypertables se a imagem não tiver TimescaleDB
STOP_SERVICES="${STOP_SERVICES:-1}"

log() { printf '\n[%s] %s\n' "$(date -u +%H:%M:%S)" "$*"; }

stop_dependent_services() {
  if [[ "${STOP_SERVICES}" != "1" ]]; then
    return 0
  fi
  log "Parando serviços que usam o Postgres (evita conflito com db_migrations no startup)..."
  (cd "$DOCKER_DIR" && docker compose stop \
    order_pickup_service \
    order_pickup_domain_event_worker \
    partner_webhook_delivery_worker \
    payment_gateway \
    billing_fiscal_service \
    2>/dev/null) || true
}

check_timescaledb() {
  if [[ "${SKIP_TIMESCALEDB:-0}" == "1" ]]; then
    log "SKIP_TIMESCALEDB=1 — fases TimescaleDB serão ignoradas."
    return 0
  fi
  if docker exec "$CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -tAc \
    "SELECT 1 FROM pg_available_extensions WHERE name = 'timescaledb'" 2>/dev/null | grep -q 1; then
    return 0
  fi
  if [[ "${SKIP_TIMESCALEDB:-0}" == "1" ]]; then
    return 0
  fi
  cat >&2 <<'EOF'

ERRO: extensão timescaledb não está disponível nesta imagem PostgreSQL.
O rebuild para na fase 01 (01_extensions_schemas.sql).

Opções:
  1) Usar imagem com TimescaleDB + PostGIS (ver docker-compose / verify-extensions.sh)
  2) Rebuild sem séries temporais: SKIP_TIMESCALEDB=1 ./run_rebuild.sh

O db_migrations.py do order_pickup NÃO é o causador deste erro.
EOF
  exit 1
}

should_run_phase() {
  local base="$1"
  if [[ -n "$ONLY_PHASE" && "$base" != ${ONLY_PHASE}* ]]; then
    return 1
  fi
  if [[ "${SKIP_TIMESCALEDB:-0}" == "1" && "$base" == "13_timescaledb_hypertables.sql" ]]; then
    return 1
  fi
  return 0
}

run_sql_file() {
  local file="$1"
  local base
  base="$(basename "$file")"
  if ! should_run_phase "$base"; then
    return 0
  fi
  log "Executando $base ..."
  local sql_path="$file"
  if [[ "${SKIP_TIMESCALEDB:-0}" == "1" && "$base" == "01_extensions_schemas.sql" ]]; then
    sql_path="${file}.notimescale.tmp"
    grep -vi timescaledb "$file" >"$sql_path" || true
  fi
  docker cp "$sql_path" "$CONTAINER:/tmp/rebuild_${base}"
  docker exec "$CONTAINER" psql -v ON_ERROR_STOP=1 -U "$DB_USER" -d "$DB_NAME" \
    -f "/tmp/rebuild_${base}"
  [[ "$sql_path" != "$file" ]] && rm -f "$sql_path"
}

wait_postgres() {
  for i in $(seq 1 60); do
    if docker exec "$CONTAINER" pg_isready -U "$DB_USER" &>/dev/null; then
      return 0
    fi
    sleep 2
  done
  echo "PostgreSQL não ficou pronto a tempo." >&2
  exit 1
}

maybe_destroy_volume() {
  if [[ "${DESTROY_VOLUME:-0}" != "1" ]]; then
    return 0
  fi
  log "DESTROY_VOLUME=1 — parando stack e removendo dados..."
  (cd "$DOCKER_DIR" && docker compose down -v)
  if [[ -d "$DOCKER_DIR/../03_data/postgres_central" ]]; then
    # rm -rf "$DOCKER_DIR/../03_data/postgres_central"
    sudo rm -rf "$DOCKER_DIR/../03_data/postgres_central"
  fi
  (cd "$DOCKER_DIR" && docker compose up -d postgres_central)
  wait_postgres
}

PHASES=(
  00_preamble.sql
  01_extensions_schemas.sql
  02_types.sql
  03_tables.sql
  03b_column_patches.sql
  04_sequences_owned_by.sql
  04b_column_defaults.sql
  05_functions.sql
  06_constraints_pk_unique_check.sql
  07_indexes.sql
  08_foreign_keys.sql
  13_timescaledb_hypertables.sql
  09_views.sql
  10_triggers.sql
  11_rls_policies.sql
  12_comments_misc.sql
  14_seed_schema_migrations.sql
)

main() {
  maybe_destroy_volume
  stop_dependent_services
  wait_postgres
  check_timescaledb

  log "Sessão: $CONTAINER / $DB_NAME"
  docker exec "$CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c \
    "SELECT current_database(), version();"

  for f in "${PHASES[@]}"; do
    path="$SCRIPT_DIR/$f"
    if [[ ! -f "$path" ]]; then
      log "Ignorando (ausente): $f"
      continue
    fi
    run_sql_file "$path"
  done

  log "Verificação rápida..."
  docker exec "$CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c \
    "SELECT COUNT(*) AS public_tables FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';"
  docker exec "$CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c \
    "SELECT extname FROM pg_extension ORDER BY 1;"
  log "Concluído."
}

main "$@"
