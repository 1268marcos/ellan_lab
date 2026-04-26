#!/usr/bin/env bash
set -euo pipefail
export BASE_URL="${BASE_URL:-http://localhost:8003}"
export OPS_TOKEN="${OPS_TOKEN:-COLE_AQUI_TOKEN_OPS}"
export RETURN_ID_REAL="${RETURN_ID_REAL:-}"
export DELIVERY_ID_REAL="${DELIVERY_ID_REAL:-}"
export REQUESTER_ID_REAL="${REQUESTER_ID_REAL:-usr_ops_001}"
export RETURN_REASON_CODE="${RETURN_REASON_CODE:-DAMAGED_ITEM}"
echo "Runbook curto L-2 D2: queue + quick actions"
echo "BASE_URL=${BASE_URL} RETURN_ID_REAL=${RETURN_ID_REAL:-<auto/fallback>}"
"/home/marcos/ellan_lab/scripts/l2_d2_ops_returns_queue_oneshot.sh"
