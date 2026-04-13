# System Overview

EthicBit / CEMU is a sovereign evidence and assurance system organized around:

1. A sovereign truth artifact:
   - `official_operational_status.json`

2. Derived technical reports:
   - `GATE_REPORT.json`
   - `technical_verification.md`

3. Assurance layer:
   - in-toto
   - SLSA provenance
   - Sigstore policy
   - verifier entrypoints

4. Canonical reconciliation path:
   - `scripts/entrypoints/reconcile_and_show_status.sh`

## Current intended good state
- `internalClosureStatus = INTERNAL_CLOSED`
- `liveStatus = PASS`
- `externalProjectionStatus = EXTERNAL_LIVE_CONVERGED`
- `officialOperationalStatus = READY`
- `reason = LIVE_CANONICAL_GATE_CONVERGED`
