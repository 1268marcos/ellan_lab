#!/usr/bin/env bash
# Money & Câmbio admin — porta fixa 8125 (evita conflito com dev local legado em 8025)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
PORT="${MONEY_CAMBIO_ADMIN_PORT:-8125}"
PID_FILE="${ROOT}/.uvicorn-${PORT}.pid"

health() {
  curl -sf "http://127.0.0.1:${PORT}/api/v1/money-cambio-admin/health" >/dev/null
}

status() {
  if health 2>/dev/null; then
    echo "money-cambio-admin: UP http://127.0.0.1:${PORT}"
    curl -s "http://127.0.0.1:${PORT}/api/v1/money-cambio-admin/health"
    echo
    return 0
  fi
  if [[ -f "${PID_FILE}" ]] && kill -0 "$(cat "${PID_FILE}")" 2>/dev/null; then
    echo "money-cambio-admin: process $(cat "${PID_FILE}") but health failed"
    return 1
  fi
  echo "money-cambio-admin: DOWN (port ${PORT})"
  return 1
}

stop() {
  if [[ -f "${PID_FILE}" ]]; then
    kill "$(cat "${PID_FILE}")" 2>/dev/null || true
    rm -f "${PID_FILE}"
  fi
  if command -v fuser >/dev/null 2>&1; then
    fuser -k "${PORT}/tcp" 2>/dev/null || true
  fi
  echo "Stopped (port ${PORT})"
}

start() {
  if health 2>/dev/null; then
    echo "Already running on port ${PORT}. Use: $0 status"
    echo "To restart: $0 restart"
    exit 0
  fi
  if ss -tln 2>/dev/null | grep -q ":${PORT} "; then
    echo "ERROR: port ${PORT} in use (Docker compose precisa desta porta)."
    echo "Libere com: ./dev.sh stop   ou: fuser -k ${PORT}/tcp"
    ss -tlnp 2>/dev/null | grep ":${PORT} " || true
    exit 1
  fi
  cd "${ROOT}"
  if [[ ! -x .venv/bin/uvicorn ]]; then
    python3 -m venv .venv
    .venv/bin/pip install -q -r requirements.txt
  fi
  PYTHONPATH=. nohup .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "${PORT}" --reload \
    >"${ROOT}/uvicorn.log" 2>&1 &
  echo $! >"${PID_FILE}"
  sleep 1
  if health; then
    echo "Started http://127.0.0.1:${PORT} (log: ${ROOT}/uvicorn.log)"
  else
    echo "Start failed. See ${ROOT}/uvicorn.log"
    exit 1
  fi
}

case "${1:-status}" in
  start) start ;;
  stop) stop ;;
  restart) stop; sleep 1; start ;;
  status) status ;;
  seed) curl -s -X POST "http://127.0.0.1:${PORT}/api/v1/money-cambio-admin/seed" | head -c 500; echo ;;
  *)
    echo "Usage: $0 {start|stop|restart|status|seed}"
    exit 1
    ;;
esac
