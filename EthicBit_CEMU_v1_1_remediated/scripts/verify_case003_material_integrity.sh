#!/usr/bin/env bash
set -euo pipefail

ROOT="artifacts/cases/case_003/canonical_root.case_003.json"
ANCHOR="artifacts/cases/case_003/anchor_verification.case_003.canonical.json"
REPORT="evidence/case003_material_integrity.log"

python3 - <<'PY' > "$REPORT"
import json
from pathlib import Path

root = Path("artifacts/cases/case_003/canonical_root.case_003.json")
anchor = Path("artifacts/cases/case_003/anchor_verification.case_003.canonical.json")

def norm(v: str) -> str:
    v = (v or "").strip().lower()
    if v.startswith("0x"):
        v = v[2:]
    return v

if not root.exists() or not anchor.exists():
    print("FAIL_CLOSED: CASE003_REQUIRED_ARTIFACT_MISSING")
    raise SystemExit(1)

root_data = json.loads(root.read_text(encoding="utf-8"))
anchor_data = json.loads(anchor.read_text(encoding="utf-8"))

root_hash = norm(root_data.get("root_hash", ""))
expected_root_hash = norm(anchor_data.get("expected_root_hash", ""))

if not root_hash or not expected_root_hash:
    print("FAIL_CLOSED: CASE003_ROOT_HASH_VALUE_MISSING")
    raise SystemExit(1)

if root_hash != expected_root_hash:
    print("FAIL_CLOSED: CASE003_ROOT_HASH_MISMATCH")
    raise SystemExit(1)

print("CASE003_MATERIAL_OK")
PY

cat "$REPORT"
