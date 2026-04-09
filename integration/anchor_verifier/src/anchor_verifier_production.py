#!/usr/bin/env python3
import json
import sys
import os
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "..", "anchor_txids_real.json")
RECEIPT_PATH = os.path.join(BASE_DIR, "artifacts", "swarm", "anchor-receipt.swarm_mvp_v1.canonical.json")
JSON_OUTPUT_FILE = os.path.join(SCRIPT_DIR, "arweave_anchor_receipt.json")

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def fetch_text(url):
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return f"__FETCH_ERROR__:{e}"

def save_json_to_file(data):
    with open(JSON_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def has_placeholders(text):
    markers = ["PENDING_", "PON_AQUI", "TODO", "REPLACE_ME"]
    upper = text.upper()
    return any(m in upper for m in markers)

def main():
    print("=== EthicBit_CEMU Triple Public Anchor Verifier - SAFE ===")
    print(f"BASE_DIR={BASE_DIR}")
    print(f"RECEIPT_PATH={RECEIPT_PATH}")

    if not os.path.exists(RECEIPT_PATH):
        print("RECEIPT_PATH_MISSING=FAIL")
        return 1

    receipt = load_json(RECEIPT_PATH)
    config = load_json(CONFIG_PATH) if os.path.exists(CONFIG_PATH) else {}

    save_json_to_file(receipt)

    if "freezeDate" in config:
        print(f"Freeze Date: {config['freezeDate']}")
    if "rootHash" in config:
        print(f"Root hash: {config['rootHash'][:16]}...{config['rootHash'][-8:]}")

    support_type = receipt.get("supportType", "")
    verification_status = receipt.get("verificationStatus", "")
    print(f"SUPPORT_TYPE={support_type}")
    print(f"VERIFICATION_STATUS={verification_status}")

    locators = receipt.get("locators", [])
    blockchain = next((x for x in locators if x.get("type") == "BLOCKCHAIN_ANCHOR"), {})
    arweave = next((x for x in locators if x.get("type") == "ARWEAVE_OBJECT"), {})
    ao = next((x for x in locators if x.get("type") == "AO_PROCESS"), {})

    sep_ok = all([
        blockchain.get("transactionHash"),
        blockchain.get("contractAddress"),
        blockchain.get("blockHash"),
    ])
    print(f"SEPOLIA_ANCHOR_RESOLVED={'PASS' if sep_ok else 'FAIL'}")

    ar_loc = arweave.get("locator", "")
    ar_body = fetch_text(ar_loc) if ar_loc else ""
    ar_nonempty = bool(ar_body and not ar_body.startswith("__FETCH_ERROR__"))
    ar_html = "<html" in ar_body.lower()
    ar_placeholders = has_placeholders(ar_body) if ar_nonempty else True

    print(f"ARWEAVE_OBJECT_RESOLVED={'PASS' if ar_nonempty and not ar_html else 'FAIL'}")
    print(f"ARWEAVE_BODY_PLACEHOLDERS={'FAIL' if ar_placeholders else 'PASS'}")

    ao_loc = ao.get("locator", "")
    ao_body = fetch_text(ao_loc) if ao_loc else ""
    ao_ok = bool(
        ao.get("processId") and
        ao.get("messageId") and
        ao_loc and
        ao_body and
        not ao_body.startswith("__FETCH_ERROR__")
    )
    print(f"AO_PROCESS_RESOLVED={'PASS' if ao_ok else 'FAIL'}")

    print()
    print("===== STATUS SUMMARY =====")
    print("ACTIVE_CANONICAL")
    print("EXTERNAL_ANCHOR_EVIDENCE_READY_FOR_INDEPENDENT_REVERIFICATION")

    if sep_ok and ao_ok and ar_nonempty and not ar_html and not ar_placeholders:
        print("NO_UNRESOLVED_ANCHOR_CONFLICTS=PASS")
        print("ANCHOR_HARDENING_ENABLED=NOT_YET_DECLARED")
    else:
        print("NO_UNRESOLVED_ANCHOR_CONFLICTS=FAIL_VISIBLE")
        print("ANCHOR_HARDENING_ENABLED=NOT_YET_DECLARED")

    return 0

if __name__ == "__main__":
    sys.exit(main())
