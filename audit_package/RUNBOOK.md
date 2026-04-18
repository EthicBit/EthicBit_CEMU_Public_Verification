# Runbook

## Canonical reconciliation command
bash ./scripts/entrypoints/reconcile_and_show_status.sh

## Expected outputs
- artifacts/history/swarm/official_operational_status.json
- results/GATE_REPORT.json
- results/technical_verification.md
- results/active/final_status_snapshot.json

## Canonical reading order
1. current_state/final_status_snapshot.json
2. current_state/official_operational_status.json
3. current_state/GATE_REPORT.json
4. current_state/technical_verification.md

## High-assurance verification
bash ./verifier/verify_all.sh --mode=high --fail-closed
