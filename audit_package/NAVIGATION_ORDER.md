# Navigation Order for External Audit

This document defines the recommended hierarchical navigation path for auditors entering the full EthicBit / CEMU repository through the terminal.

## 1. Repository base path

/Users/oskrmiranda/Documentos/EthicBit_CEMU

## 2. Recommended audit entry path

/Users/oskrmiranda/Documentos/EthicBit_CEMU/audit_package

This is the curated external-audit entrypoint.

## 3. Hierarchical navigation order

### Level 0 - Curated audit intake
Start here:
- audit_package/COVER_LETTER_EXTERNAL_AUDIT.md
- audit_package/README.md
- audit_package/SCOPE.md
- audit_package/SYSTEM_OVERVIEW.md
- audit_package/THREAT_MODEL.md
- audit_package/ASSUMPTIONS_AND_TRUST_BOUNDARIES.md
- audit_package/RUNBOOK.md

### Level 1 - Current packaged state
Then read:
- audit_package/current_state/final_status_snapshot.json
- audit_package/current_state/official_operational_status.json
- audit_package/current_state/GATE_REPORT.json
- audit_package/current_state/technical_verification.md

### Level 2 - Canonical repository references
Then review:
- docs/REPO_AUDIT_TRUTH_MODEL.md
- docs/CANONICAL_WORKFLOWS.md
- docs/ETHICBIT_AUDIT_GRADE_STATUS.md
- AUDIT_START_HERE.md

### Level 3 - Sovereign truth in the repository
Then inspect:
- artifacts/history/swarm/official_operational_status.json

This is the canonical final operational truth artifact.

### Level 4 - Derived active repository outputs
Then inspect:
- results/active/final_status_snapshot.json
- results/GATE_REPORT.json
- results/technical_verification.md

### Level 5 - Canonical reconciliation path
Then inspect and, if needed, execute:
- scripts/entrypoints/reconcile_and_show_status.sh

### Level 6 - Assurance layer
Then inspect:
- assurance/in-toto/
- assurance/slsa/
- assurance/sigstore/
- attestations/
- verifier/verify_all.sh

### Level 7 - Operational source code
Finally, if deeper review is required:
- scripts/status/official_operational_status_calculator.py
- scripts/run_mixed_audience_audit.sh
- scripts/run_production_readiness.sh

## 4. Authority rule

If any conflict exists between artifacts, authority is resolved in this order:

1. artifacts/history/swarm/official_operational_status.json
2. results/GATE_REPORT.json
3. results/technical_verification.md
4. audit_package/
5. docs/

## 5. Practical terminal sequence

Recommended starting commands:

cd "/Users/oskrmiranda/Documentos/EthicBit_CEMU/audit_package"
sed -n '1,220p' COVER_LETTER_EXTERNAL_AUDIT.md
cat current_state/final_status_snapshot.json
cat current_state/official_operational_status.json

If deeper repository review is required:

cd "/Users/oskrmiranda/Documentos/EthicBit_CEMU"
sed -n '1,220p' AUDIT_START_HERE.md
cat artifacts/history/swarm/official_operational_status.json
bash ./scripts/entrypoints/reconcile_and_show_status.sh

## 6. Summary

External auditors should move through the repository in this order:

audit_package -> current_state -> references/docs -> sovereign truth -> derived outputs -> reconciliation entrypoint -> assurance -> operational code

This navigation order is intended to minimize ambiguity and ensure that audit conclusions are grounded in sovereign operational truth rather than stale or secondary artifacts.
