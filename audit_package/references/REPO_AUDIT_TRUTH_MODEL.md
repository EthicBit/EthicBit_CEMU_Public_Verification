# REPO AUDIT TRUTH MODEL

## Level 1 - Sovereign official truth
Canonical source of final operational truth:
- artifacts/history/swarm/official_operational_status.json

This artifact prevails over all derived reports.

## Level 2 - Technical derived artifacts
- results/GATE_REPORT.json
- results/technical_verification.md
- results/index.json

These are corroborative, not sovereign.

## Level 3 - Assurance and policy artifacts
- assurance/in-toto/root.layout
- assurance/slsa/provenance.json
- assurance/sigstore/policy.json
- attestations/slsa_l4_final_attestation.json

## Conflict rule
If there is any conflict:
1. official_operational_status.json
2. GATE_REPORT.json
3. technical_verification.md

## Canonical reconciliation sequence
1. python3 scripts/status/official_operational_status_calculator.py
2. bash ./scripts/run_mixed_audience_audit.sh --all
3. Read artifacts/history/swarm/official_operational_status.json
4. Corroborate with results/GATE_REPORT.json and results/technical_verification.md
