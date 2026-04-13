#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

AUDIT_RISK_MODE="${ETHICBIT_AUDIT_RISK_MODE:-HIGH}"
AUDIT_REQUIRE_HYBRID="${ETHICBIT_AUDIT_REQUIRE_HYBRID:-1}"

echo "===== ETHICBIT_CEMU FULL AUDIT ====="
echo "ROOT=$ROOT"
date -u

require_env() {
  local name="$1"
  if [ -z "${!name:-}" ]; then
    echo "FAIL: missing env var $name"
    exit 1
  fi
}

echo
echo "===== 0. ENV CHECK ====="
require_env ETHICBIT_ED25519_SIGN_CMD
require_env ETHICBIT_MLDSA_SIGN_CMD
require_env ETHICBIT_ED25519_VERIFY_CMD
require_env ETHICBIT_MLDSA_VERIFY_CMD
require_env ETHICBIT_ED25519_KEY_ID
require_env ETHICBIT_MLDSA_KEY_ID

python3 --version
which openssl
openssl version

echo
echo "===== 1. PYTHON SYNTAX CHECK ====="
python3 -m py_compile \
  scripts/crypto/hybrid_sign.py \
  scripts/crypto/hybrid_verify.py \
  scripts/status/official_operational_status_calculator.py
echo "PY_COMPILE=PASS"

echo
echo "===== 2. LIVE ANCHOR VERIFICATION ====="
python3 integration/anchor_verifier/src/anchor_verifier_production.py

echo
echo "===== 3. HYBRID E2E POSITIVE TEST ====="
cat > /tmp/ethicbit_hybrid_payload.json <<'JSON'
{
  "artifactType": "ethicbit_hybrid_signature_test",
  "buildId": "audit-build-current-state",
  "claim": "ETHICBIT_HYBRID_SIGNATURE_TEST",
  "timestamp": "2026-04-12T18:00:00Z"
}
JSON

python3 - <<'PY'
import json
from pathlib import Path
from scripts.crypto.jcs_rfc8785 import canonicalize_bytes
raw = json.loads(Path("/tmp/ethicbit_hybrid_payload.json").read_text(encoding="utf-8"))
Path("/tmp/ethicbit_hybrid_payload.verify.jcs.json").write_bytes(canonicalize_bytes(raw))
print("WROTE=/tmp/ethicbit_hybrid_payload.verify.jcs.json")
PY

python3 scripts/crypto/hybrid_sign.py \
  /tmp/ethicbit_hybrid_payload.json \
  --output /tmp/ethicbit_signature_set.json \
  --risk-mode "$AUDIT_RISK_MODE" \
  --ed25519-sign-cmd "$ETHICBIT_ED25519_SIGN_CMD" \
  --mldsa-sign-cmd "$ETHICBIT_MLDSA_SIGN_CMD" \
  --ed25519-key-id "$ETHICBIT_ED25519_KEY_ID" \
  --mldsa-key-id "$ETHICBIT_MLDSA_KEY_ID"

python3 scripts/crypto/hybrid_verify.py \
  --payload /tmp/ethicbit_hybrid_payload.verify.jcs.json \
  --signature-set /tmp/ethicbit_signature_set.json \
  --risk-mode "$AUDIT_RISK_MODE" \
  --ed25519-verify-cmd "$ETHICBIT_ED25519_VERIFY_CMD" \
  --mldsa-verify-cmd "$ETHICBIT_MLDSA_VERIFY_CMD"

echo
echo "===== 4. DIRECT SIGNATURE CONSISTENCY ====="
./assurance/signers/ed25519_sign.sh /tmp/ethicbit_hybrid_payload.verify.jcs.json > /tmp/ed25519_direct.sig
DIRECT_SIG="$(cat /tmp/ed25519_direct.sig)"
SET_SIG="$(python3 - <<'PY'
import json
d=json.load(open('/tmp/ethicbit_signature_set.json'))
print([x for x in d['signatures'] if x['algorithm']=='ED25519'][0]['signature'])
PY
)"
echo "DIRECT_LEN=${#DIRECT_SIG}"
echo "SET_LEN=${#SET_SIG}"
if [ "$DIRECT_SIG" = "$SET_SIG" ]; then
  echo "ED25519_SIG_MATCH=YES"
else
  echo "ED25519_SIG_MATCH=NO"
  exit 1
fi

echo
echo "===== 5. TAMPER NEGATIVE TEST ====="
cp /tmp/ethicbit_hybrid_payload.verify.jcs.json /tmp/ethicbit_hybrid_payload.tampered.json
python3 - <<'PY'
from pathlib import Path
p=Path("/tmp/ethicbit_hybrid_payload.tampered.json")
txt=p.read_text(encoding="utf-8")
txt=txt.replace("ETHICBIT_HYBRID_SIGNATURE_TEST","ETHICBIT_HYBRID_SIGNATURE_TEST_TAMPERED")
p.write_text(txt, encoding="utf-8")
print("TAMPERED=YES")
PY

set +e
python3 scripts/crypto/hybrid_verify.py \
  --payload /tmp/ethicbit_hybrid_payload.tampered.json \
  --signature-set /tmp/ethicbit_signature_set.json \
  --risk-mode "$AUDIT_RISK_MODE" \
  --ed25519-verify-cmd "$ETHICBIT_ED25519_VERIFY_CMD" \
  --mldsa-verify-cmd "$ETHICBIT_MLDSA_VERIFY_CMD"
RC=$?
set -e

if [ "$RC" -eq 0 ]; then
  echo "FAIL: tamper test unexpectedly passed"
  exit 1
fi
echo "TAMPER_TEST=PASS_EXPECTED_FAIL"

echo
echo "===== 6. OFFICIAL STATUS RECALC ====="
python3 scripts/status/official_operational_status_calculator.py \
  --risk-mode "$AUDIT_RISK_MODE" \
  --require-hybrid \
  --require-signature \
    --ed25519-sign-cmd "$ETHICBIT_ED25519_SIGN_CMD" \
    --mldsa-sign-cmd "$ETHICBIT_MLDSA_SIGN_CMD" \
    --ed25519-verify-cmd "$ETHICBIT_ED25519_VERIFY_CMD" \
    --mldsa-verify-cmd "$ETHICBIT_MLDSA_VERIFY_CMD" \
    --ed25519-key-id "$ETHICBIT_ED25519_KEY_ID" \
    --mldsa-key-id "$ETHICBIT_MLDSA_KEY_ID"
else
  python3 scripts/status/official_operational_status_calculator.py \
    --risk-mode "$AUDIT_RISK_MODE" \
    --ed25519-sign-cmd "$ETHICBIT_ED25519_SIGN_CMD" \
    --mldsa-sign-cmd "$ETHICBIT_MLDSA_SIGN_CMD" \
    --ed25519-verify-cmd "$ETHICBIT_ED25519_VERIFY_CMD" \
    --mldsa-verify-cmd "$ETHICBIT_MLDSA_VERIFY_CMD" \
    --ed25519-key-id "$ETHICBIT_ED25519_KEY_ID" \
    --mldsa-key-id "$ETHICBIT_MLDSA_KEY_ID"
fi

echo
echo "===== 7. OFFICIAL STATUS SUMMARY ====="
python3 - <<'PY'
import json
p='artifacts/history/swarm/official_operational_status.json'
d=json.load(open(p))
summary = {
  "officialStatus": d.get("officialStatus"),
  "reason": d.get("reason"),
  "internalClosureStatus": d.get("internalClosureStatus"),
  "externalProjectionStatus": d.get("externalProjectionStatus"),
  "internalCryptographyStatus": d.get("internalCryptographyStatus"),
  "externalCryptographyStatus": d.get("externalCryptographyStatus"),
  "signature": d.get("signature",{}).get("status"),
  "signatureSet": d.get("signatureSet",{}).get("status"),
  "signatureVerification": d.get("signatureVerification",{}).get("status"),
  "missingOrInvalidAlgorithms": d.get("signatureVerification",{}).get("missingOrInvalidAlgorithms",[])
}
print(json.dumps(summary, indent=2, ensure_ascii=False))

assert summary["officialStatus"] == "READY", summary
assert summary["externalCryptographyStatus"] == "PASS", summary
assert summary["signature"] == "SIGNED_HYBRID", summary
assert summary["signatureSet"] == "PASS", summary
assert summary["signatureVerification"] == "PASS", summary
PY

echo
echo "===== 8. ARTIFACT PRESENCE ====="
python3 - <<'PY'
import os
paths = [
  "artifacts/history/swarm/official_operational_status.json",
  "results/GATE_REPORT.json",
  "artifacts/history/swarm/triple_public_anchor_live_verification.json",
  "integration/anchor_verifier/anchor_txids_real.json",
  "PACKAGE_MANIFEST.json",
  "publication/publication_state.json"
]
missing = []
for p in paths:
    ok = os.path.exists(p)
    print(f"{p} -> {'OK' if ok else 'MISSING'}")
    if not ok:
        missing.append(p)
if missing:
    raise SystemExit("missing required artifacts: " + ", ".join(missing))
PY

echo
echo "AUDIT_RESULT=PASS"
echo "ETHICBIT_CEMU current state verified end-to-end"
