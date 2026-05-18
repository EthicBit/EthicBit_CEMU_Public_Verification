# Release Checklist — EthicBit/CEMU

**Version:** 1.0 | **Date:** 2026-05-18  
**Machine-readable policy:** `assurance/anchor/anchor-policy.json`

Use this checklist before executing any anchor operation or promoting a release.
Check each item. A single unchecked item blocks the release for its class.

---

## CONTROLLED_EVIDENCE release

- [ ] All tests pass: `pytest tests/ -q`
- [ ] Claim boundary: `python3 tools/external_validation/claim_red_team/run_claim_red_team.py --dry-run` → `block_rate=100%`
- [ ] SBOM KMS signature present: `assurance/sbom/aem_v1_1_sbom.cyclonedx.sig.json` exists and `algorithm: ECDSA_SHA_256`
- [ ] Triple anchor gate passes: `bash deployment/anchor_pre_deploy_gate.sh`
- [ ] `external_claim_review_completed` = false in all public artifacts
- [ ] `human_attestation_status` = HUMAN_ATTESTATION_PENDING (not elevated)
- [ ] No live AWS IDs in staged files: `python3 scripts/hooks/check_no_aws_ids.py <changed files>`
- [ ] `git ls-remote origin main` and `git ls-remote mirror main` both at same commit after push

---

## EXTERNAL_VALIDATION release

All CONTROLLED_EVIDENCE items, plus:

- [ ] All 6 in-toto statements KMS-signed: `assurance/in-toto/attestation-index.json` status = `KMS_SIGNED_PENDING_EXTERNAL_WITNESS`
- [ ] `slsa-build.yml` ran successfully on the release commit (check Actions tab)
- [ ] `assurance/slsa/subject-index.json` — all subjects `digest_status: BOUND`
- [ ] Claim consistency check passes: `python3 scripts/hooks/check_claim_consistency.py`
- [ ] `level4-policy.json` → `full_l4_claim_allowed: false`
- [ ] Outreach pack current: `docs/external-validation/outreach/V4_0_EXTERNAL_REVIEWER_OUTREACH_PACK.md` reflects current criteria status
- [ ] Threat model current: `assurance/threat-model/threat-model.json` — no new HIGH threats without mitigation

---

## PRODUCTION_RELEASE

All EXTERNAL_VALIDATION items, plus:

- [ ] In-toto chain externally witnessed (attestation-index status = `EXTERNALLY_WITNESSED`)
- [ ] `human_attestation_status` = `HUMAN_ATTESTED` with signed human attestation document
- [ ] External validation criteria: minimum 5/8 CONTROLLED_PASS, criteria 1+2+8 resolved
- [ ] `full_l4_claim_allowed` review — update only after confirming all L4 prerequisites met
- [ ] Human reviewer sign-off on anchor operation (GATE_HUMAN_REVIEW)
- [ ] Mainnet KZG blob anchor authorized and receipt saved to `assurance/v4_0/`
- [ ] SBOM re-signed if any components changed since last signing
- [ ] All 6 in-toto statements re-signed if payload changed since last signing

---

## Post-release

- [ ] Mirror push verified: `git ls-remote mirror main` = `git ls-remote origin main`
- [ ] Anchor receipt committed: `assurance/v4_0/V4_0_*_ANCHOR_RECEIPT.json`
- [ ] Status bulletin updated in `docs/STATUS_BULLETIN_PUBLIC_*.md`
- [ ] `assurance/anchor/anchor-policy.json` `current_state` block updated

---

## Blocking conditions (any → ABORT)

| Condition | Action |
|-----------|--------|
| `block_rate_percent < 100` | Fix CBE before proceeding |
| `full_l4_claim_allowed: true` without external witness | Revert field |
| Live AWS ID found in changed files | Sanitize before push |
| Hypothesis test failure | Fix before merge |
| Mirror diverged from origin | Resolve before release |
