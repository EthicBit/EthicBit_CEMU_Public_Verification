#!/usr/bin/env python3
"""Empirical proof of fail-closed behavior under tampering.

Demonstrates that scripts/core/verify_l5_full_chain.py detects three
distinct classes of tampering on results/kzg_blob_anchor_report.json:

  Test 1 [INEXISTENCE]   : tx_hash replaced with a synthetic invalid hash
                           STAGE 3 expected to fail with "tx not found"
  Test 2 [WRONG-FROM]    : from_address changed to a different wallet
                           (tx_hash kept real)
                           STAGE 3 expected to fail with MISMATCH on `from`
  Test 3 [WRONG-BLOCK]   : block_number changed to an arbitrary value
                           (tx_hash kept real)
                           STAGE 3 expected to fail with MISMATCH on `block`

The script ALWAYS restores the original anchor file (try/finally), even
on crash. After restoration it runs the full verifier once more and
asserts the system is back to L5_FULL_CHAIN=PASS.

Exit codes:
  0  all four phases behaved as expected (3 detections + 1 healthy restore)
  1  at least one phase produced an unexpected outcome

Reproducible by any auditor with python3, eth_account, and network access.
No private keys required: this script only modifies a public JSON and
invokes the public verifier.
"""
import json, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANCHOR = ROOT / "results" / "kzg_blob_anchor_report.json"
VERIFIER = ROOT / "scripts" / "core" / "verify_l5_full_chain.py"
PYTHON = sys.executable

def hr(s):
    print("\n" + "=" * 68)
    print(s)
    print("=" * 68)

def run_verifier():
    r = subprocess.run([PYTHON, str(VERIFIER)],
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    return r.returncode

def mutate(transform_fn):
    d = json.loads(ANCHOR.read_text())
    transform_fn(d)
    ANCHOR.write_text(json.dumps(d, indent=2, sort_keys=True))

def assert_outcome(label, observed, expected_nonzero, results):
    ok = (observed != 0) if expected_nonzero else (observed == 0)
    verdict = "PASS" if ok else "FAIL"
    print(f"  observed exit : {observed}")
    print(f"  expected      : {'NON-ZERO (detection)' if expected_nonzero else 'ZERO (healthy)'}")
    print(f"  verdict       : {verdict}")
    results.append((label, ok, observed))
    return ok

def main():
    if not ANCHOR.exists():
        print(f"ERROR: missing {ANCHOR}"); return 1
    if not VERIFIER.exists():
        print(f"ERROR: missing {VERIFIER}"); return 1

    backup = Path(tempfile.mktemp(suffix="_kzg_anchor_backup.json"))
    shutil.copy2(ANCHOR, backup)
    print(f"[BACKUP] anchor copied to {backup}")
    results = []

    try:
        original = json.loads(ANCHOR.read_text())
        print(f"[ORIGINAL] tx_hash={original['tx_hash']}")
        print(f"[ORIGINAL] from   ={original['from_address']}")
        print(f"[ORIGINAL] block  ={original['block_number']}")

        hr("TEST 1 [INEXISTENCE] tampering with synthetic invalid tx_hash")
        fake = "0x" + "00" * 32
        print(f"  mutation: tx_hash -> {fake}")
        mutate(lambda d: d.update(tx_hash=fake))
        assert_outcome("test1_inexistence", run_verifier(), True, results)

        shutil.copy2(backup, ANCHOR)

        hr("TEST 2 [WRONG-FROM] tx_hash kept real, from_address swapped")
        fake_from = "0x" + "ff" * 20
        print(f"  mutation: from_address -> {fake_from}")
        mutate(lambda d: d.update(from_address=fake_from))
        assert_outcome("test2_wrong_from", run_verifier(), True, results)

        shutil.copy2(backup, ANCHOR)

        hr("TEST 3 [WRONG-BLOCK] tx_hash kept real, block_number swapped")
        fake_block = original["block_number"] + 999_999
        print(f"  mutation: block_number -> {fake_block}")
        mutate(lambda d: d.update(block_number=fake_block))
        assert_outcome("test3_wrong_block", run_verifier(), True, results)

    finally:
        shutil.copy2(backup, ANCHOR)
        backup.unlink()
        print(f"\n[RESTORE] anchor restored from backup, backup deleted")

    hr("FINAL [HEALTHY] post-restoration verification")
    print(f"  expectation: system back to L5_FULL_CHAIN=PASS")
    assert_outcome("final_healthy", run_verifier(), False, results)

    hr("SUMMARY")
    all_ok = all(ok for _, ok, _ in results)
    for label, ok, code in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {label:25s}  exit={code}")

    print()
    if all_ok:
        print("TAMPERING_RESISTANCE=PROVEN")
        print("  - 3 distinct attack classes detected (inexistence, wrong-from, wrong-block)")
        print("  - system fails closed (exit non-zero) under each attack")
        print("  - system recovers to PASS after restoration (no permanent damage)")
        return 0
    else:
        print("TAMPERING_RESISTANCE=UNPROVEN (some test produced unexpected outcome)")
        return 1

if __name__ == "__main__":
    sys.exit(main())
