#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

runtime_path = ROOT / "results" / "runtime_evidence_strength_report.json"
ceiling_path = ROOT / "results" / "constitutional_evidence_ceiling.json"
anchor_path = ROOT / "results" / "l5_onchain_anchor_report.json"

def load_json(path: Path):
    if not path.exists():
        return None, f"MISSING:{path.relative_to(ROOT)}"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as e:
        return None, f"UNREADABLE:{path.relative_to(ROOT)}:{e}"

runtime, err = load_json(runtime_path)
if err:
    print(f"FAIL_CLOSED: {err}")
    sys.exit(1)

ceiling, err = load_json(ceiling_path)
if err:
    print(f"FAIL_CLOSED: {err}")
    sys.exit(1)

anchor, err = load_json(anchor_path)
if err:
    print(f"FAIL_CLOSED: {err}")
    sys.exit(1)

errors = []

def expect(payload, key, expected, label):
    actual = payload.get(key)
    if actual != expected:
        errors.append(f"{label}.{key}={actual!r} expected {expected!r}")

expect(runtime, "claim_level_ceiling", "L5", "runtime")
expect(runtime, "eligible_for_l5", True, "runtime")

expect(ceiling, "current_ceiling", "L5", "ceiling")
expect(ceiling, "eligible_for_l5", True, "ceiling")

# anclaje L5: acepta varios esquemas razonables
anchor_status = str(anchor.get("status") or anchor.get("verification_status") or "").upper()
if anchor_status not in {"PASS", "ONCHAIN_ANCHOR_VERIFIED", "VERIFIED", "L5_ONCHAIN_ANCHOR_VERIFIED"}:
    errors.append(f"anchor.status={anchor_status!r} not accepted")

tx_hash = (
    anchor.get("tx_hash")
    or anchor.get("transaction_hash")
    or anchor.get("txHash")
)
if not isinstance(tx_hash, str) or not tx_hash.startswith("0x") or len(tx_hash) < 10:
    errors.append(f"anchor.tx_hash invalid: {tx_hash!r}")

if errors:
    print("FAIL_CLOSED: L5 canonical state not satisfied")
    for e in errors:
        print(f" - {e}")
    sys.exit(1)

print("L5_CANONICAL_STATE=PASS")
print("runtime.claim_level_ceiling=L5")
print("ceiling.claim_level_ceiling=L5")
print(f"anchor.status={anchor_status}")
print(f"anchor.tx_hash={tx_hash}")
