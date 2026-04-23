#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

GH_BIN="${GH_BIN:-}"
if [[ -z "${GH_BIN}" ]]; then
  if command -v gh >/dev/null 2>&1; then
    GH_BIN="$(command -v gh)"
  elif [[ -x "${ROOT_DIR}/.tools/gh/bin/gh" ]]; then
    GH_BIN="${ROOT_DIR}/.tools/gh/bin/gh"
  fi
fi

if [[ -z "${GH_BIN}" ]]; then
  echo "Erro: GitHub CLI (gh) não encontrado no PATH nem em .tools/gh/bin/gh." >&2
  echo "Instale o gh e autentique com permissões de admin no repositório." >&2
  exit 1
fi

REPO_SLUG="${REPO_SLUG:-1268marcos/ellan_lab}"
TARGET_BRANCH="${TARGET_BRANCH:-main}"

echo "Aplicando branch protection em ${REPO_SLUG}:${TARGET_BRANCH}"
echo "- Smoke obrigatório em PR"
echo "- Full obrigatório para merge em ${TARGET_BRANCH}"
echo ""

"${GH_BIN}" api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  "/repos/${REPO_SLUG}/branches/${TARGET_BRANCH}/protection" \
  --input - <<'JSON'
{
  "required_status_checks": {
    "strict": true,
    "checks": [
      { "context": "Sprint5 Item5 Smoke", "app_id": -1 },
      { "context": "Sprint5 Item5 Regression", "app_id": -1 }
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 1,
    "require_last_push_approval": false
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": true,
  "lock_branch": false,
  "allow_fork_syncing": true
}
JSON

echo ""
echo "OK: branch protection aplicada com sucesso."
