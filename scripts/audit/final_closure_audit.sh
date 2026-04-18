#!/usr/bin/env bash
set -euo pipefail

# Avoid runtime bytecode drift in strict freeze executions.
export PYTHONDONTWRITEBYTECODE=1

ROOT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

REQUIRE_CLEAN_TREE="${ETHICBIT_REQUIRE_CLEAN_TREE:-0}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --require-clean-tree)
      REQUIRE_CLEAN_TREE="1"
      shift
      ;;
    --functional-only)
      REQUIRE_CLEAN_TREE="0"
      shift
      ;;
    *)
      echo "Unknown option: $1" >&2
      echo "Usage: $0 [--require-clean-tree|--functional-only]" >&2
      exit 2
      ;;
  esac
done

echo "=============================================="
echo "FINAL CLOSURE AUDIT — ETHICBIT / CEMU"
echo "=============================================="
echo

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

echo "=== 1. GIT / TAG STATUS ==="
git status --short || true
echo
echo "HEAD: $(git rev-parse --short HEAD)"
echo "TAG CHECK:"
git show --stat --oneline v2.2b-constitutional-amendment | head -20
echo

if [[ "$REQUIRE_CLEAN_TREE" == "1" ]]; then
  echo "=== 1B. CLEAN TREE ENFORCEMENT (STRICT FREEZE) ==="
  if [[ -n "$(git status --porcelain)" ]]; then
    fail "working tree is not clean (strict freeze mode)"
  fi
  echo "OK: clean working tree verified"
  echo
else
  echo "INFO: clean-tree enforcement disabled (functional/audit closure mode)"
  echo
fi

echo "=== 2. ETHIC MECHANICS AUDIT ==="
./scripts/audit/audit_ethic_mechanics.sh
echo

echo "=== 3. OFFICIAL OPERATIONAL STATUS ==="
./scripts/status/official_operational_status_calculator.py --root . --strict --require-signature
echo

echo "=== 4. CRYPTOGRAPHY / SIGNATURE STATUS ==="
python3 - <<'PY'
import json
from pathlib import Path

p = Path("artifacts/history/swarm/official_operational_status.json")
data = json.loads(p.read_text(encoding="utf-8"))

print("officialOperationalStatus =", data.get("officialOperationalStatus"))
print("internalCryptographyStatus =", data.get("internalCryptographyStatus"))
print("externalCryptographyStatus =", data.get("externalCryptographyStatus"))
print("signature.status =", data.get("signature", {}).get("status"))

if data.get("officialOperationalStatus") != "READY":
    raise SystemExit("officialOperationalStatus != READY")
if data.get("internalCryptographyStatus") != "PASS":
    raise SystemExit("internalCryptographyStatus != PASS")
if data.get("externalCryptographyStatus") != "PASS":
    raise SystemExit("externalCryptographyStatus != PASS")
if data.get("signature", {}).get("status") != "SIGNED_HYBRID":
    raise SystemExit("signature.status != SIGNED_HYBRID")
PY
echo

echo "=== 5. MIXED AUDIENCE AUDIT + CONSTITUTIONAL AMENDMENT ==="
./scripts/run_mixed_audience_audit_with_constitutional_amendment.sh
echo

echo "=== 6. CONSTITUTIONAL AMENDMENT OUTPUTS ==="
test -f results/constitutional_amendment_snapshot.json || fail "missing results/constitutional_amendment_snapshot.json"
grep -q 'AMENDMENT-TECHNICAL-SCOPE-DETECTABLE-ENTITIES-v1.0' results/constitutional_amendment_snapshot.json || fail "snapshot missing amendment_id"
grep -q 'TECHNICAL_EXPANDED' results/constitutional_amendment_snapshot.json || fail "snapshot missing TECHNICAL_EXPANDED"
grep -q 'RULE-ETHIC-TEC-DET-004-v1.0' results/constitutional_amendment_snapshot.json || fail "snapshot missing RULE-ETHIC-TEC-DET-004-v1.0"

grep -q '"constitutionalAmendment"' results/constitutional_controls_report.json || fail "constitutional_controls_report missing constitutionalAmendment"
grep -q 'constitutional_amendment_snapshot.json' results/constitutional_controls_report.json || fail "constitutional_controls_report missing snapshot path"
grep -q 'RULE-ETHIC-TEC-DET-004-v1.0' results/constitutional_controls_report.json || fail "constitutional_controls_report missing RULE-ETHIC-TEC-DET-004-v1.0"

grep -q 'Constitutional Amendment Snapshot' results/technical_verification.md || fail "technical_verification missing amendment section"
grep -q 'TECHNICAL_EXPANDED' results/technical_verification.md || fail "technical_verification missing TECHNICAL_EXPANDED"
grep -q 'RULE-ETHIC-TEC-DET-004-v1.0' results/technical_verification.md || fail "technical_verification missing RULE-ETHIC-TEC-DET-004-v1.0"
echo "OK: constitutional amendment outputs verified"
echo

echo "=== 7. AUDIT PACKAGE CURRENT STATE ==="
python3 - <<'PY'
import json
from pathlib import Path

idx = json.loads(Path("audit_package/current_state/index.json").read_text(encoding="utf-8"))
gate = json.loads(Path("audit_package/current_state/GATE_REPORT.json").read_text(encoding="utf-8"))
ops = json.loads(Path("audit_package/current_state/official_operational_status.json").read_text(encoding="utf-8"))

print("packState =", idx["verifiedState"]["packState"])
print("externalAnchorState =", idx["verifiedState"]["externalAnchorState"])
print("operationalReadiness =", idx["verifiedState"]["operationalReadiness"])
print("officialStatus =", ops["officialOperationalStatus"])
print("gate official status =", gate["stateModel"]["officialOperationalStatusObserved"])

if idx["verifiedState"]["packState"] != "ACTIVE_CANONICAL":
    raise SystemExit("packState != ACTIVE_CANONICAL")
if idx["verifiedState"]["externalAnchorState"] != "ANCHOR_HARDENING_ENABLED":
    raise SystemExit("externalAnchorState != ANCHOR_HARDENING_ENABLED")
if idx["verifiedState"]["operationalReadiness"] != "READY_FOR_CONTROLLED_PRODUCTION":
    raise SystemExit("operationalReadiness != READY_FOR_CONTROLLED_PRODUCTION")
if ops["officialOperationalStatus"] != "READY":
    raise SystemExit("officialOperationalStatus != READY")
if gate["stateModel"]["officialOperationalStatusObserved"] != "READY":
    raise SystemExit("gate official status != READY")
PY
echo

echo "=== 8. CI SECRETS ==="
gh secret list | grep -E 'ETHICBIT_ED25519_PRIVATE_KEY_PEM|ETHICBIT_ED25519_PUBLIC_KEY_PEM|ETHICBIT_MLDSA_PRIVATE_KEY_PEM|ETHICBIT_MLDSA_PUBLIC_KEY_PEM' >/dev/null || fail "missing one or more CI secrets"
gh secret list | grep -E 'ETHICBIT_ED25519_PRIVATE_KEY_PEM|ETHICBIT_ED25519_PUBLIC_KEY_PEM|ETHICBIT_MLDSA_PRIVATE_KEY_PEM|ETHICBIT_MLDSA_PUBLIC_KEY_PEM'
echo

echo "=== 9. FINAL GIT STATE ==="
git status --short || true
echo

echo "=============================================="
echo "FINAL CLOSURE AUDIT: PASS"
echo "READY FOR FREEZE"
echo "=============================================="
