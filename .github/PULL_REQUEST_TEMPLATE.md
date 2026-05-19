## Summary

Describe the change and the intended impact.

## PR Gate checklist (automated — all must pass)

- [ ] `claim-boundary` — 14 cases, block_rate=100%
- [ ] `property-tests` — Hypothesis I-1..I-M, 8 tests pass
- [ ] `consistency-check` — attestation-index + SLSA policy consistent
- [ ] `lint` — ruff + mypy clean
- [ ] `no-aws-ids` — no live AWS IDs in changed files

## Governance checklist (manual)

- [ ] Base branch is `main`
- [ ] `full_l4_claim_allowed` not changed to `true` without external witness
- [ ] `human_attestation_status` not elevated without out-of-band authorization
- [ ] `external_claim_review_completed` remains `false` unless human-attested
- [ ] Constitutional check `production-distributed-ready-final` passed
- [ ] Release discipline check `release-grade-discipline-gate` passed
- [ ] If claim semantics changed → `docs/policies/CLAIMS_POLICY.md` updated

## Evidence (when applicable)

- `assurance/in-toto/attestation-index.json`
- `assurance/anchor/anchor-policy.json`
- `artifacts/history/swarm/official_operational_status.json`
