#!/usr/bin/env bash
set -euo pipefail

: "${STRICT_BASE_IMAGE:?Set STRICT_BASE_IMAGE to a real pinned image ref, e.g. ghcr.io/org/img@sha256:<64hex>}"

cd "$(dirname "$0")/../.."

rm -rf out cache/solidity-files-cache.json
export CI=1
export TZ=UTC
export LC_ALL=C
export LANG=C
export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-$(git log -1 --pretty=%ct)}"

npm ci --ignore-scripts
npm run build:hermetic

python3 scripts/assurance/write_hermetic_build_report.py \
  --mode strict_hermetic \
  --strict-required \
  --network-mode none \
  --base-image-ref "$STRICT_BASE_IMAGE" \
  --lockfile package-lock.json \
  --lockfile requirements.txt \
  --output results/hermetic_build_report.json

bash scripts/verify_closure_integrity.sh

jq -e '.hermetic_mode == "strict_hermetic"' results/hermetic_build_report.json >/dev/null
echo "STRICT_HERMETIC=PASS"
