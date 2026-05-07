#!/usr/bin/env bash
# Verify Ed25519 signatures on the AEM-EVOLVE Multi-Agent API demo receipt and manifest.
# Requires: openssl, python3
# Usage: bash verify_demo_receipt_signatures.sh
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../../.." && pwd)"

SIGNATURE_SET="${REPO_ROOT}/assurance/evolve-multi-agent/AEM_EVOLVE_MULTI_AGENT_API_SIGNATURE_SET.json"
PUBKEY="${REPO_ROOT}/assurance/evolve-multi-agent/AEM_EVOLVE_MULTI_AGENT_API_DEMO_PUBLIC_KEY.pem"

[ -f "$SIGNATURE_SET" ] || { echo "ERROR: signature set not found: $SIGNATURE_SET" >&2; exit 1; }
[ -f "$PUBKEY" ] || { echo "ERROR: public key not found: $PUBKEY" >&2; exit 1; }

echo "=== AEM-EVOLVE MULTI-AGENT API DEMO SIGNATURE VERIFICATION ==="
echo "public_key   = $PUBKEY"
echo "sig_set      = $SIGNATURE_SET"
echo ""

OVERALL=PASS

python3 - "$SIGNATURE_SET" "$PUBKEY" "$REPO_ROOT" <<'PYEOF'
import base64, hashlib, json, os, subprocess, sys, tempfile
from pathlib import Path

sig_set_path, pubkey_path, repo_root = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
sig_set = json.loads(sig_set_path.read_text(encoding="utf-8"))

overall = True
for subject in sig_set["subjects"]:
    name = subject["name"]
    artifact_path = repo_root / subject["path"]
    expected_sha = subject["canonical_sha256"]
    sig_b64 = subject["signature_b64"]

    print(f"--- {name} ---")
    print(f"  path               = {subject['path']}")

    if not artifact_path.exists():
        print(f"  ERROR: file not found")
        overall = False
        continue

    obj = json.loads(artifact_path.read_text(encoding="utf-8"))
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    computed_sha = hashlib.sha256(canonical).hexdigest()

    print(f"  canonical_sha256   = {computed_sha}")
    if computed_sha != expected_sha:
        print(f"  HASH_CHECK         = FAIL (expected {expected_sha})")
        overall = False
        continue
    print(f"  HASH_CHECK         = PASS")

    sig_bytes = base64.b64decode(sig_b64)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as tf_payload:
        tf_payload.write(canonical)
        tf_payload_name = tf_payload.name
    with tempfile.NamedTemporaryFile(delete=False, suffix=".sig") as tf_sig:
        tf_sig.write(sig_bytes)
        tf_sig_name = tf_sig.name
    try:
        result = subprocess.run(
            ["openssl", "pkeyutl", "-verify", "-pubin", "-inkey", str(pubkey_path),
             "-rawin", "-in", tf_payload_name, "-sigfile", tf_sig_name],
            capture_output=True
        )
        sig_ok = result.returncode == 0
    finally:
        os.unlink(tf_payload_name)
        os.unlink(tf_sig_name)

    if sig_ok:
        print(f"  SIGNATURE_VERIFY   = PASS")
    else:
        print(f"  SIGNATURE_VERIFY   = FAIL")
        overall = False

    print("")

sys.exit(0 if overall else 1)
PYEOF

RC=$?
if [ $RC -eq 0 ]; then
  echo ""
  echo "AEM_EVOLVE_MULTI_AGENT_API_DEMO_SIGNATURE_STATUS=PASS"
  echo "NOTE: Demo key only — not HSM-backed, not third-party attested."
else
  echo ""
  echo "AEM_EVOLVE_MULTI_AGENT_API_DEMO_SIGNATURE_STATUS=FAIL"
  exit 1
fi
