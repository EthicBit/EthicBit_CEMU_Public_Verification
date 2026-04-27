# Verification Reproducible Guide — EthicBit/CEMU

Date: 2026-04-27
Purpose: Allow a third party or internal reviewer to reproduce the core constitutional, probative, and realtime snapshot checks.

## 1. Repository State

Recommended branch:

    git checkout final/addendum-v3-universal-closure
    git pull

Relevant validated commits:

    0ecd7131 — publish claim_level_ceiling in constitutional evidence ceiling
    05ced3e4 — add canonical realtime millisecond snapshot guard
    77539bdc — validate realtime millisecond snapshot guard

## 2. Constitutional Gate

    bash scripts/audit/verify_constitutional_controls.sh

Expected result:

    CONSTITUTIONAL_STATUS=PASS

## 3. Realtime Snapshot Guard

    python3 scripts/realtime/realtime_snapshot_guard.py
    python3 scripts/realtime/verify_realtime_snapshot_guard.py

Expected result:

    REALTIME_SNAPSHOT_GUARD=PASS
    constitutional_equivalence=True
    claim_level_ceiling=L5

## 4. Realtime Daemon Probe Evidence

    cat results/realtime_daemon_probe_report.json

Expected properties:

    status=PASS
    constitutional_equivalence=true
    ticks_blocked=0
    fail_closed_policy=true

## 5. Anti-Tampering Principle

The realtime snapshot guard must fail closed if the canonical snapshot is modified without regenerating its fingerprint.

Expected failure reason for basic tamper:

    SNAPSHOT_FINGERPRINT_MISMATCH

## 6. Third-Party Boundary

    cat docs/third_party_representation_boundary.md

EthicBit/CEMU is suitable for external presentation, audit, review, or reception, but does not automatically bind third parties or replace sovereign authorities.
