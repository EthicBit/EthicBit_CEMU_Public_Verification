# Assumptions and Trust Boundaries

## Assumptions
- Active state must be read from the reconciled current artifacts
- Derived reports are valid only after reconciliation
- Historical artifacts may remain in the repository but are not sovereign

## Trust boundaries
- Sovereign truth boundary:
  `artifacts/history/swarm/official_operational_status.json`

- Derived technical boundary:
  `results/GATE_REPORT.json`
  `results/technical_verification.md`

- Assurance boundary:
  `assurance/`
  `attestations/`
  `verifier/`

## Rule
When trust boundaries disagree, sovereign truth prevails.
