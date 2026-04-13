# AUDIT START HERE

## Canonical audit entrypoint

Run:

bash ./scripts/entrypoints/reconcile_and_show_status.sh

## Truth hierarchy

### Level 1 - Sovereign official truth
- artifacts/history/swarm/official_operational_status.json

If any conflict exists between artifacts, this file prevails.

### Level 2 - Technical derived artifacts
- results/GATE_REPORT.json
- results/technical_verification.md

### Level 3 - Assurance and policy layer
- assurance/in-toto/root.layout
- assurance/slsa/provenance.json
- assurance/sigstore/policy.json
- attestations/slsa_l4_final_attestation.json

## Current expected good state
- internalClosureStatus = INTERNAL_CLOSED
- liveStatus = PASS
- externalProjectionStatus = EXTERNAL_LIVE_CONVERGED
- officialOperationalStatus = READY
- reason = LIVE_CANONICAL_GATE_CONVERGED
