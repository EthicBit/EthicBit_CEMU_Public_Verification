# Final Release Approval Checklist (Pre-Real-Closure)

Use this checklist before declaring real closure.

## 1. Scope and Branch Integrity

- [ ] Release source branch is `main`.
- [ ] No official claim is sourced from experimental-only branches.
- [ ] Final claim artifacts are committed and tagged.

Evidence:

- `README.md`
- `CONTRIBUTING.md`
- tag reference and commit SHA

## 2. Required Merge Controls

- [ ] `production-distributed-ready-final` passed.
- [ ] `release-grade-discipline-gate` passed.
- [ ] Branch protection for `main` enforces required checks.

Evidence:

- `.github/workflows/production-distributed-ready-final.yml`
- `.github/workflows/release-grade-discipline-gate.yml`
- repository branch protection settings

## 3. Constitutional and Mechanical Ethics

- [ ] Constitutional controls report generated and audited.
- [ ] Mechanical ethics audit executed with multisector rules.
- [ ] Critical controls preserve `FAIL_CLOSED` behavior.

Evidence:

- `results/constitutional_controls_report.json`
- `scripts/audit/verify_constitutional_controls.sh`
- `scripts/audit/audit_ethic_mechanics.sh`

## 4. Cryptographic and Official Status

- [ ] Official status calculator executed in strict signature mode.
- [ ] Hybrid signing state validated (`SIGNED_HYBRID` when required).
- [ ] External crypto verification path is fail-closed.

Evidence:

- `artifacts/history/swarm/official_operational_status.json`
- `assurance/signers/mldsa_verify.sh`
- `scripts/status/official_operational_status_calculator.py`

## 5. Freeze Discipline

- [ ] Functional closure passed.
- [ ] Strict clean-tree check passed for final freeze.
- [ ] No uncommitted drift within official claim perimeter.

Evidence:

- `scripts/audit/final_closure_audit.sh`
- `results/release_discipline_report.json`
- `git status --porcelain`

## 6. Public Claim Consistency

- [ ] State taxonomy matches current artifacts.
- [ ] Public bulletin and technical/legal/regulatory outputs are aligned.
- [ ] No mixed terminology (`candidate` vs promoted state) in official outputs.

Evidence:

- `docs/STATE_TAXONOMY_OFFICIAL.md`
- `docs/STATUS_BULLETIN_PUBLIC_2026-04-18.md`
- `results/index.json`
- `results/GATE_REPORT.json`

## 7. External Reproducibility Validation

- [ ] Independent rerun produced reproducible decision outputs.
- [ ] Hashes and signatures validated externally.
- [ ] Deviations and residual risks were documented.

Evidence:

- third-party execution log
- reproducibility digest
- signed closure addendum

## 8. Final Sign-Off

- [ ] Engineering lead approval
- [ ] Security/Crypto approval
- [ ] Compliance/Legal approval
- [ ] Operations approval

Record:

- Approval date:
- Release/freeze tag:
- Decision: `GO` or `NO-GO`
- Residual risks accepted:
