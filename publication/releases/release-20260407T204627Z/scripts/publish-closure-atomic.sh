#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${1:-$(cd -- "${SCRIPT_DIR}/.." && pwd)}"
PUBLICATION_ROOT="${2:-${ROOT_DIR}/publication}"
TARGET_REL="${3:-}"
VERIFY_SCRIPT="${ROOT_DIR}/scripts/verify_closure_integrity.sh"

fail() {
  local code="$1"
  shift
  printf '%s: %s\n' "$code" "$*" >&2
  exit 1
}

[[ -n "$TARGET_REL" ]] || fail "USAGE" "publish-closure-atomic.sh <root_dir> <publication_root> <target_rel>"
[[ -x "$VERIFY_SCRIPT" ]] || fail "NOT_READY (FAIL-CLOSED)" "verify_closure_integrity.sh must be executable"

TARGET_DIR="${PUBLICATION_ROOT}/${TARGET_REL}"
[[ -d "$TARGET_DIR" ]] || fail "NOT_READY (FAIL-CLOSED)" "target release directory missing: $TARGET_DIR"

"$VERIFY_SCRIPT" "$ROOT_DIR" >/dev/null

mkdir -p "$PUBLICATION_ROOT"
ln -sfn "$TARGET_REL" "${PUBLICATION_ROOT}/active"

PUBLISHED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
cat > "${PUBLICATION_ROOT}/publication_state.json" <<EOF
{
  "state": "ACTIVE_CANONICAL",
  "activeTarget": "${TARGET_REL}",
  "publishedAt": "${PUBLISHED_AT}"
}
EOF

printf 'ACTIVE_CANONICAL\n'