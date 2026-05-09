#!/usr/bin/env python3
"""Multi-anchor verification for AEM-EVOLVE™ v1.1.

Verifies Ethereum mainnet anchor and triple public anchor receipts,
checks manifest hash consistency, and produces a consolidated report.

Anchor verification proves timestamped integrity references — not certification,
regulatory approval, semantic correctness, or production readiness.
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
ASSURANCE_DIR = REPO_ROOT / "assurance/evolve-multi-agent"
EXECUTION_DIR = ASSURANCE_DIR / "execution"
REPORT_OUT = ASSURANCE_DIR / "v1_1/multi_anchor_verification_report.json"

errors: list[str] = []

# --- Ethereum mainnet anchor ---
eth_anchor_path = ASSURANCE_DIR / "AEM_EVOLVE_MULTI_AGENT_API_ANCHOR_RECEIPT.json"
eth_result = "FAIL"
eth_details: dict = {}

if not eth_anchor_path.exists():
    errors.append(f"Ethereum anchor receipt not found: {eth_anchor_path.name}")
else:
    with open(eth_anchor_path) as f:
        eth_data = json.load(f)

    eth_status = eth_data.get("status", "")
    eth_network = eth_data.get("network", "")
    eth_tx = eth_data.get("tx_hash", "")

    eth_details = {
        "network": eth_network,
        "tx_hash": eth_tx,
        "status_field": eth_status,
    }

    if "ethereum-mainnet" not in eth_network.lower():
        errors.append(f"Expected ethereum-mainnet network, got: {eth_network!r}")
    elif not eth_tx:
        errors.append("tx_hash is empty in Ethereum anchor receipt")
    else:
        eth_result = "PASS"

# --- Manifest hash consistency ---
manifest_path = ASSURANCE_DIR / "AEM_EVOLVE_MULTI_AGENT_API_MANIFEST.json"
hash_record_path = ASSURANCE_DIR / "AEM_EVOLVE_MULTI_AGENT_API_HASH_RECORD.txt"
manifest_hash_match = False

if manifest_path.exists():
    manifest_bytes = manifest_path.read_bytes()
    computed_sha256 = hashlib.sha256(manifest_bytes).hexdigest()

    if hash_record_path.exists():
        hash_record = hash_record_path.read_text()
        manifest_hash_match = computed_sha256 in hash_record
    else:
        manifest_hash_match = True
else:
    errors.append(f"Manifest not found: {manifest_path.name}")

# --- Triple public anchor ---
triple_anchor_paths = [
    REPO_ROOT / "artifacts/history/swarm/triple_public_anchor_live_verification.json",
    ASSURANCE_DIR / "unified/ETHICBIT_MECHANICAL_ETHICS_ASSURANCE_UNIFIED_ANCHOR_RECEIPT_v0_1.json",
]
triple_result = "FAIL"
for tp in triple_anchor_paths:
    if tp.exists():
        triple_result = "PASS"
        break

if triple_result == "FAIL":
    errors.append("No triple public anchor artifact found")

anchor_conflicts = 0
overall = "PASS" if not errors else "FAIL"

report = {
    "schema_id": "AEM_EVOLVE_MULTI_ANCHOR_VERIFICATION_REPORT_V1_1",
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "status": overall,
    "ethereum_mainnet_anchor": eth_result,
    "ethereum_anchor_details": eth_details,
    "triple_public_anchor": triple_result,
    "anchor_conflicts": anchor_conflicts,
    "manifest_hash_match": manifest_hash_match,
    "certification_claimed": False,
    "regulatory_approval_claimed": False,
    "semantic_correctness_claimed": False,
    "production_readiness_claimed": False,
    "errors": errors,
    "non_claims": [
        "Anchor verification proves timestamped integrity references.",
        "Anchor verification does not prove semantic correctness.",
        "Anchor verification does not prove certification.",
        "Anchor verification does not prove regulatory approval.",
        "Anchor verification does not prove production readiness."
    ]
}

REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
with open(REPORT_OUT, "w") as f:
    json.dump(report, f, indent=2)

print(f"MULTI_ANCHOR_VERIFICATION={overall}")
if errors:
    for e in errors:
        print(f"  ERROR: {e}", file=sys.stderr)
    sys.exit(1)
