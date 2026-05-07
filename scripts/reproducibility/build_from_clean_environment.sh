#!/usr/bin/env bash
set -euo pipefail

echo "=== AEM V1.1 REPRODUCIBILITY EXTENSION ==="
echo "current_closure=PUBLIC_REPRODUCIBLE_VERIFICATION_SUPPORT"
echo "target_closure=INDEPENDENTLY_REPRODUCED_RELEASE_BUILD"
echo

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

echo "=== REPO STATUS ==="
git rev-parse --short HEAD
git status --short
echo

echo "=== DECLARED SUBJECTS ==="
test -f assurance/reproducibility/declared_subjects.json
echo "declared_subjects=OK"
echo

echo "=== EXPECTED HASHES ==="
test -f assurance/reproducibility/expected_hashes.json
echo "expected_hashes=OK"
echo

echo "=== COMPARISON ==="
python3 scripts/reproducibility/compare_reproducible_outputs.py
echo

echo "=== REPRODUCTION REPORT ==="
python3 scripts/reproducibility/generate_reproducibility_report.py
echo

echo "REPRODUCIBILITY_EXTENSION_STATUS=PASS"
echo "current_closure=PUBLIC_REPRODUCIBLE_VERIFICATION_SUPPORT"
echo "target_closure=INDEPENDENTLY_REPRODUCED_RELEASE_BUILD"

