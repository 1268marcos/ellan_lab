#!/usr/bin/env bash
set -euo pipefail

# Atalho padrão da equipe para rodar o smoke FA-5 Timescale em 1 comando.
# Uso:
#   ./02_docker/run_fa5_timescale_smoke.sh
# Opcional via env:
#   POSTGRES_CONTAINER=postgres_central POSTGRES_DB=locker_central POSTGRES_USER=admin ./02_docker/run_fa5_timescale_smoke.sh

POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-postgres_central}"
POSTGRES_DB="${POSTGRES_DB:-locker_central}"
POSTGRES_USER="${POSTGRES_USER:-admin}"
SCRIPT_PATH_LOCAL="${SCRIPT_PATH_LOCAL:-/home/marcos/ellan_lab/02_docker/postgres_central/ops/smoke_fa5_timescale.sql}"
SCRIPT_PATH_REMOTE="${SCRIPT_PATH_REMOTE:-/tmp/smoke_fa5_timescale.sql}"

if [[ ! -f "$SCRIPT_PATH_LOCAL" ]]; then
  echo "Smoke SQL não encontrado em: $SCRIPT_PATH_LOCAL" >&2
  exit 1
fi

echo "==> Copiando smoke SQL para o container: $POSTGRES_CONTAINER"
docker cp "$SCRIPT_PATH_LOCAL" "${POSTGRES_CONTAINER}:${SCRIPT_PATH_REMOTE}"

echo "==> Executando smoke FA-5 Timescale no banco: $POSTGRES_DB"
docker exec "$POSTGRES_CONTAINER" sh -lc \
  "psql -U \"$POSTGRES_USER\" -d \"$POSTGRES_DB\" -v ON_ERROR_STOP=1 -f \"$SCRIPT_PATH_REMOTE\""

echo "==> Smoke FA-5 Timescale finalizado com sucesso."
