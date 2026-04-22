#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

echo "=== HISTORICAL HYGIENE DEEP DRY RUN ==="
echo "repo: $ROOT_DIR"
echo

echo "[1] Current object store footprint"
git count-objects -vH
echo

echo "[2] Tracked file counts for high-risk hygiene classes"
printf '.venv-mythril tracked: '
git ls-files '.venv-mythril/**' | wc -l | tr -d ' '
printf '\n'
printf '*.pyc tracked: '
git ls-files '*.pyc' | wc -l | tr -d ' '
printf '\n'
printf '__pycache__ tracked paths: '
git ls-files | grep -c '__pycache__' || true
printf '\n'
printf 'node_modules tracked: '
git ls-files 'node_modules/**' | wc -l | tr -d ' '
printf '\n\n'

echo "[3] Largest historical blobs (top 30)"
git rev-list --objects --all \
  | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' \
  | awk '$1=="blob"{print $3, $2, substr($0, index($0,$4))}' \
  | sort -nr \
  | head -30
echo

echo "[4] Non-destructive rewrite plan preview"
cat <<'EOF'
- Freeze window and comms plan.
- Full backup mirror before rewrite:
  git clone --mirror <repo-url> ../EthicBit_CEMU.mirror.backup.git
- Analyze candidates:
  git filter-repo --analyze
- Rewrite candidates (execute only in approved maintenance window):
  git filter-repo --path .venv-mythril --invert-paths
  git filter-repo --path-glob '*.pyc' --invert-paths
  git filter-repo --path-glob '**/__pycache__/*' --invert-paths
- Re-tag/re-validate closure artifacts and publish migration notice.
EOF
echo

echo "dry-run complete"
