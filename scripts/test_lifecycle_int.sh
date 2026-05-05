#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${ROOT}/scripts/docker-compose.lifecycle-int.yml"
SEED_SQL="${ROOT}/scripts/seed_lifecycle_int.sql"

: "${LIFECYCLE_INT_PG_PORT:=15432}"
: "${LIFECYCLE_INT_OLS_PORT:=18010}"
: "${LIFECYCLE_INT_OLS_B_PORT:=18011}"
: "${LIFECYCLE_INT_FE_PORT:=15173}"
export LIFECYCLE_INT_PG_PORT LIFECYCLE_INT_OLS_PORT LIFECYCLE_INT_OLS_B_PORT LIFECYCLE_INT_FE_PORT

log() { printf '[lifecycle-int] %s\n' "$*" >&2; }

pickup_metrics_total() {
  python3 -c 'import json,sys; print(int(json.load(sys.stdin)["total_terminal_pickups"]))'
}

wait_http() {
  local url="$1" name="$2" max="${3:-90}"
  local i=0
  while [[ "$i" -lt "$max" ]]; do
    if curl -sfS "$url" >/dev/null 2>&1; then
      log "ok $name"
      return 0
    fi
    i=$((i + 1))
    sleep 2
  done
  log "timeout $name ($url)"
  return 1
}

cd "$ROOT"

log "compose down (cleanup)"
docker compose -f "$COMPOSE_FILE" down -v --remove-orphans 2>/dev/null || true

log "compose up"
docker compose -f "$COMPOSE_FILE" up -d --build

log "wait postgres"
docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U admin -d locker_central >/dev/null 2>&1 || sleep 3
wait_http "http://127.0.0.1:${LIFECYCLE_INT_OLS_PORT}/health" "ols_a" 90
wait_http "http://127.0.0.1:${LIFECYCLE_INT_OLS_B_PORT}/health" "ols_b" 90

log "seed db"
docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U admin -d locker_central -v ON_ERROR_STOP=1 <"$SEED_SQL"

log "wait frontend (vite)"
wait_http "http://127.0.0.1:${LIFECYCLE_INT_FE_PORT}/api/order-lifecycle/health" "vite_proxy" 180

log "curl internal metrics (db)"
curl -sfS "http://127.0.0.1:${LIFECYCLE_INT_OLS_PORT}/internal/analytics/pickup-metrics" \
  -H "X-Internal-Token: dev-internal-token" | python3 -c 'import json,sys; json.load(sys.stdin)' >/dev/null

log "partner isolation alpha"
A="$(curl -sfS "http://127.0.0.1:${LIFECYCLE_INT_OLS_PORT}/partner/analytics/pickup-metrics" -H "X-Partner-Id: partner-alpha" | pickup_metrics_total)"
log "partner isolation beta"
B="$(curl -sfS "http://127.0.0.1:${LIFECYCLE_INT_OLS_PORT}/partner/analytics/pickup-metrics" -H "X-Partner-Id: partner-beta" | pickup_metrics_total)"

if [[ "$A" != "1" ]]; then
  log "expected alpha total_terminal_pickups=1 got $A"
  echo FAIL
  exit 1
fi
if [[ "$B" != "2" ]]; then
  log "expected beta total_terminal_pickups=2 got $B"
  echo FAIL
  exit 1
fi

log "frontend->backend via proxy"
FE="$(curl -sfS "http://127.0.0.1:${LIFECYCLE_INT_FE_PORT}/api/order-lifecycle/health" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("status",""))')"
if [[ "$FE" != "ok" ]]; then
  log "frontend proxy health status expected ok got $FE"
  echo FAIL
  exit 1
fi

log "second FastAPI health"
curl -sfS "http://127.0.0.1:${LIFECYCLE_INT_OLS_B_PORT}/health" | python3 -c 'import json,sys; assert json.load(sys.stdin).get("database")=="ok"' >/dev/null

echo ALL_PASS
