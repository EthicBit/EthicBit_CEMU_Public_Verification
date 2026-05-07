#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${1:-$(cd -- "${SCRIPT_DIR}/.." && pwd)}"

fail() {
  local code="$1"
  shift
  echo "${code}: $*" >&2
  exit 1
}

require_file() {
  local path="$1"
  [[ -f "$path" ]] || fail "VERIFY_FAIL" "missing required file: ${path#${ROOT_DIR}/}"
}

MANIFEST="${ROOT_DIR}/assurance/release/AEM_V1_1_SUPPLY_CHAIN_VERIFICATION_MANIFEST.json"
MANIFEST_JCS="${ROOT_DIR}/assurance/release/AEM_V1_1_SUPPLY_CHAIN_VERIFICATION_MANIFEST.jcs.json"
HASH_RECORD="${ROOT_DIR}/assurance/release/AEM_V1_1_SUPPLY_CHAIN_VERIFICATION_HASH_RECORD.txt"
TOOLCHAIN="${ROOT_DIR}/assurance/toolchain/toolchain_fingerprint.json"
SBOM_CDX="${ROOT_DIR}/assurance/sbom/aem_v1_1_sbom.cyclonedx.json"
SBOM_SPDX="${ROOT_DIR}/assurance/sbom/aem_v1_1_sbom.spdx.json"
PROV_JSON="${ROOT_DIR}/assurance/provenance/SLSA_PROVENANCE.json"
SIG_SET="${ROOT_DIR}/assurance/signatures/AEM_V1_1_SUPPLY_CHAIN_SIGNATURE_SET.json"
SIG_VERIFY_REPORT="${ROOT_DIR}/assurance/signatures/AEM_V1_1_SUPPLY_CHAIN_SIGNATURE_VERIFICATION.json"
EXT_RECEIPT="${ROOT_DIR}/receipts/AEM_V1_1_SUPPLY_CHAIN_VERIFICATION_EXTENSION_RECEIPT.json"
REGISTRY="${ROOT_DIR}/registry/ETHICBIT_CEMU_AEM_V1_1_GLOBAL_PUBLIC_VERIFICATION_REGISTRY.json"
REGISTRY_HASH_RECORD="${ROOT_DIR}/registry/ETHICBIT_CEMU_AEM_V1_1_GLOBAL_PUBLIC_VERIFICATION_REGISTRY_HASH_RECORD.txt"
REGISTRY_RECEIPT="${ROOT_DIR}/receipts/ETHICBIT_CEMU_AEM_V1_1_GLOBAL_PUBLIC_VERIFICATION_REGISTRY_MAINNET_ANCHOR_RECEIPT.json"
MASTER_CLOSURE="${ROOT_DIR}/results/master_closure_report.json"
CONSTITUTIONAL="${ROOT_DIR}/results/constitutional_controls_report.json"

for f in \
  "$MANIFEST" "$MANIFEST_JCS" "$HASH_RECORD" \
  "$TOOLCHAIN" "$SBOM_CDX" "$SBOM_SPDX" "$PROV_JSON" \
  "$SIG_SET" "$SIG_VERIFY_REPORT" "$EXT_RECEIPT" \
  "$REGISTRY" "$REGISTRY_HASH_RECORD" "$REGISTRY_RECEIPT" \
  "$MASTER_CLOSURE" "$CONSTITUTIONAL"; do
  require_file "$f"
done

python3 - "$ROOT_DIR" <<'PY'
import hashlib
import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])

manifest = json.loads((root / "assurance/release/AEM_V1_1_SUPPLY_CHAIN_VERIFICATION_MANIFEST.json").read_text(encoding="utf-8"))
manifest_jcs = (root / "assurance/release/AEM_V1_1_SUPPLY_CHAIN_VERIFICATION_MANIFEST.jcs.json").read_bytes()
hash_record = (root / "assurance/release/AEM_V1_1_SUPPLY_CHAIN_VERIFICATION_HASH_RECORD.txt").read_text(encoding="utf-8")
registry = json.loads((root / "registry/ETHICBIT_CEMU_AEM_V1_1_GLOBAL_PUBLIC_VERIFICATION_REGISTRY.json").read_text(encoding="utf-8"))
registry_hash_record = (root / "registry/ETHICBIT_CEMU_AEM_V1_1_GLOBAL_PUBLIC_VERIFICATION_REGISTRY_HASH_RECORD.txt").read_text(encoding="utf-8")
registry_receipt = json.loads((root / "receipts/ETHICBIT_CEMU_AEM_V1_1_GLOBAL_PUBLIC_VERIFICATION_REGISTRY_MAINNET_ANCHOR_RECEIPT.json").read_text(encoding="utf-8"))
master = json.loads((root / "results/master_closure_report.json").read_text(encoding="utf-8"))
constitutional = json.loads((root / "results/constitutional_controls_report.json").read_text(encoding="utf-8"))
signature_report = json.loads((root / "assurance/signatures/AEM_V1_1_SUPPLY_CHAIN_SIGNATURE_VERIFICATION.json").read_text(encoding="utf-8"))
extension_receipt = json.loads((root / "receipts/AEM_V1_1_SUPPLY_CHAIN_VERIFICATION_EXTENSION_RECEIPT.json").read_text(encoding="utf-8"))

def fail(msg: str) -> None:
    print(f"VERIFY_FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)

if manifest.get("claim_level") != "PUBLIC_REPRODUCIBLE_VERIFICATION_SUPPORT":
    fail("manifest claim_level mismatch")

if manifest.get("not_claimed", {}).get("fully_reproducible_build") is not False:
    fail("manifest not_claimed.fully_reproducible_build must be false")

if manifest.get("relationship_to_canonical", {}).get("mutates_aem_v1_1_canonical") is not False:
    fail("extension must not mutate canonical artifact")

subjects = manifest.get("subjects", [])
if not isinstance(subjects, list) or not subjects:
    fail("manifest subjects missing")

for subject in subjects:
    rel = subject.get("path")
    expected = str(subject.get("sha256", "")).lower()
    if not rel or not expected:
        fail("invalid subject entry")
    path = root / rel
    if not path.exists():
        fail(f"missing subject file: {rel}")
    current = hashlib.sha256(path.read_bytes()).hexdigest().lower()
    if current != expected:
        fail(f"subject hash mismatch: {rel}")

record_match = re.search(
    r"SHA-256 \(canonicalized JSON: RFC8785 canonical form\):\s*([0-9a-fA-F]{64})",
    hash_record,
    flags=re.S,
)
if not record_match:
    fail("manifest hash record canonical hash not found")
record_canonical = record_match.group(1).lower()
current_manifest_canonical = hashlib.sha256(manifest_jcs).hexdigest().lower()
if record_canonical != current_manifest_canonical:
    fail("manifest canonical hash mismatch against hash record")

registry_expected_match = re.search(
    r"SHA-256 \(canonicalized JSON:[^)]+\):\s*([0-9a-fA-F]{64})",
    registry_hash_record,
    flags=re.S,
)
if not registry_expected_match:
    fail("registry canonical hash missing in registry hash record")
registry_expected = registry_expected_match.group(1).lower()
registry_current = hashlib.sha256(
    json.dumps(registry, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
).hexdigest()
if registry_expected != registry_current:
    fail("registry canonical hash mismatch")

manifest_registry = manifest.get("registry_reference", {})
if manifest_registry.get("canonical_sha256", "").lower() != registry_current:
    fail("manifest registry canonical reference mismatch")

if registry_receipt.get("status") != "ONCHAIN_REGISTRY_ANCHOR_VERIFIED":
    fail("registry receipt status not verified")
if registry_receipt.get("network") != "ethereum-mainnet":
    fail("registry receipt network mismatch")
if int(registry_receipt.get("chain_id", 0)) != 1:
    fail("registry receipt chain id mismatch")

if master.get("status") != "PASS":
    fail("master closure status is not PASS")
summary = master.get("summary", {})
if summary.get("constitutional_status") != "PASS":
    fail("master closure constitutional_status is not PASS")
if summary.get("claim_level_ceiling") != "L5":
    fail("master closure claim_level_ceiling is not L5")
if summary.get("anti_re_status") != "PASS":
    fail("master closure anti_re_status is not PASS")

constitutional_summary = constitutional.get("summary", {})
if int(constitutional_summary.get("total", 0)) != 14:
    fail("constitutional controls total must be 14")
if int(constitutional_summary.get("passed", 0)) != 14:
    fail("constitutional controls passed must be 14")
if int(constitutional_summary.get("failed", 1)) != 0:
    fail("constitutional controls failed must be 0")

if signature_report.get("status") != "PASS":
    fail("signature verification report is not PASS")
if extension_receipt.get("status") not in {"PASS", "PARTIAL_PASS_UNSIGNED"}:
    fail("extension receipt has invalid status")

print("VERIFY_RELEASE_STATUS=PASS")
print("claim_level=PUBLIC_REPRODUCIBLE_VERIFICATION_SUPPORT")
print(f"registry_anchor_tx={registry_receipt.get('tx_hash')}")
print(f"registry_anchor_block={registry_receipt.get('block_number')}")
print(f"manifest_canonical_sha256={current_manifest_canonical}")
print(f"manifest_jcs_sha256={hashlib.sha256(manifest_jcs).hexdigest()}")
PY

PATH="/opt/homebrew/opt/openssl@3/bin:${PATH}" python3 "${ROOT_DIR}/scripts/crypto/hybrid_verify.py" \
  --payload "${MANIFEST_JCS}" \
  --signature-set "${SIG_SET}" \
  --ed25519-verify-cmd "assurance/signers/ed25519_verify.sh {payload} {signature}" \
  --mldsa-verify-cmd "assurance/signers/mldsa_verify.sh {payload} {signature}" >/tmp/ethicbit_verify_release_sig.out 2>/tmp/ethicbit_verify_release_sig.err \
  || fail "VERIFY_FAIL" "hybrid signature verification command failed"

echo "SIGNATURE_VERIFICATION=PASS"
echo "RELEASE_VERIFICATION=PASS"
