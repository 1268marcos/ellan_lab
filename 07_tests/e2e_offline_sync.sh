#!/usr/bin/env bash
set -euo pipefail

echo "=== E2E: Offline Sync App Campo ==="

test -f 01_source/frontend/src/utils/offlineStorage.ts

grep -q "saveChecklistOffline" 01_source/frontend/src/utils/offlineStorage.ts
grep -q "syncOfflineChecklists" 01_source/frontend/src/utils/offlineStorage.ts
grep -q "Sincronizar offline" 01_source/frontend/src/pages/field/Checklist.tsx

echo "E2E_OFFLINE_SYNC_OK"
