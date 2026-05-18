# Incident Runbook — EthicBit/CEMU

**Version:** 1.0 | **Date:** 2026-05-18  
**Severity scale:** P0 (immediate) / P1 (same day) / P2 (next business day)

---

## Incident 1 — KMS Signing Key Compromise

**Severity:** P0  
**Indicators:** Unauthorized KMS Sign API calls in CloudTrail; unexpected signature in any statement; AWS alerts.

**Response:**

1. **Disable key immediately** — AWS Console → KMS → `alias/ethicbit-intoto-signing` → Disable Key. Do NOT delete (needed for forensics).
2. **Revoke IAM credentials** used in the unauthorized call.
3. **Identify scope** — run `aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=Sign` to enumerate all Sign calls since last authorized use.
4. **Mark all signed artifacts as SUSPECT** — update `assurance/in-toto/attestation-index.json` status to `COMPROMISE_SUSPECTED`; update `assurance/sbom/aem_v1_1_sbom.cyclonedx.json` signature block.
5. **Create new KMS key** — new alias, new IAM policy; do not reuse compromised key.
6. **Re-sign all artifacts** — run `scripts/crypto/sign_intoto_statements_kms.py` and `scripts/crypto/sign_sbom_kms.py` with new key.
7. **Notify external validators** — if outreach has been initiated, inform pending validators that prior signatures are invalidated.
8. **Commit, push, re-anchor** — new signatures require a new anchor operation at minimum EXTERNAL_VALIDATION class.
9. **Post-incident** — document root cause in `assurance/security/`; update threat model STR-001 mitigation if new control added.

**Recovery gate:** New signatures verified via KMS Verify API before any public claim using signed artifacts is re-activated.

---

## Incident 2 — Fraudulent Anchor Receipt

**Severity:** P1  
**Indicators:** `anchor_pre_deploy_gate.sh` fails; TXID not found on Sepolia/Arweave/AO; anchor receipt file modified in git.

**Response:**

1. **Stop all release operations** — no new anchor until resolved.
2. **Verify each network independently:**
   - Sepolia: `cast tx <txid> --rpc-url <sepolia-rpc>` — confirm contract address and data.
   - Arweave: `curl https://arweave.net/<txid>` — confirm content hash.
   - AO: verify message ID at AO gateway.
3. **Identify which anchor is fraudulent** — compare `integration/anchor_verifier/anchor_txids_real.json` with live network state.
4. **Check git history** — `git log --follow -p integration/anchor_verifier/anchor_txids_real.json` to find when the file changed.
5. **Revert fraudulent file** — `git revert <commit>` (do not `git reset --hard`).
6. **Re-execute anchor** — run the appropriate anchor script (e.g., `scripts/core/anchor_v4_0_controlled_evidence_mainnet.py`) with `DRY_RUN=1` first to validate.
7. **Commit new receipt** — include forensic note in commit message referencing the incident.

**Recovery gate:** `anchor_pre_deploy_gate.sh` passes cleanly before releasing.

---

## Incident 3 — Claim Boundary Bypass Attempt

**Severity:** P1  
**Indicators:** CI `claim-boundary` job fails; `block_rate_percent < 100`; `overclaims_failed_to_block > 0`.

**Response:**

1. **Block the PR** — do not merge until resolved. The CI gate enforces this automatically.
2. **Identify the failing case** — check CI output for `case_id` and `decision` != BLOCKED.
3. **Review the cases file** — was `claim_boundary_regression_cases.json` modified? If so, check the diff: was a case removed, or was `expected_decision` changed?
4. **Check `evaluate_case` logic** — was `run_claim_red_team.py` modified to weaken evaluation?
5. **Restore the blocking** — either revert the cases file change or add the missing `permitted_alternative`/`required_external_condition` field.
6. **Verify Hypothesis tests still pass** — `pytest tests/test_claim_boundary_properties.py -v`.
7. **If new legitimate claim needs to be expressed** — follow the "Adding a New Claim" process in `docs/policies/CLAIMS_POLICY.md`.

**Recovery gate:** `block_rate=100%` and all Hypothesis tests pass.

---

## Incident 4 — CI/CD Pipeline Compromise

**Severity:** P0  
**Indicators:** Unexpected workflow run producing attestations; unauthorized push to main; GitHub security alert.

**Response:**

1. **Rotate GitHub Actions secrets immediately** — GitHub Settings → Secrets → rotate all repository secrets.
2. **Revoke compromised PAT or OIDC token** if applicable.
3. **Audit recent workflow runs** — Actions tab → filter by `slsa-build.yml` and `slsa_hybrid_attest.yml` — verify all runs were triggered by legitimate commits.
4. **Invalidate any attestations produced in the compromised window** — mark affected provenance artifacts with `INTEGRITY_SUSPECT`.
5. **Review `CODEOWNERS`** — ensure no unauthorized changes to protected paths.
6. **Pin action versions** — if a marketplace action was unpinned, pin to SHA immediately.
7. **Force-push protection** — verify branch protection is still active on main: `gh api repos/{owner}/{repo}/branches/main/protection`.
8. **Re-run hermetic build** on a clean runner after credentials rotated; produce new build manifest and attestations.

**Recovery gate:** Clean workflow run with new credentials; attestations re-produced; security review of all changes in compromised window.

---

## Incident 5 — Mirror Divergence

**Severity:** P2  
**Indicators:** `git ls-remote mirror main` ≠ `git ls-remote origin main`; mirror push rejected.

**Response:**

1. **Identify divergence** — `git log origin/main..mirror/main` and `git log mirror/main..origin/main`.
2. **Never force-push to mirror without understanding the divergence** — check if mirror has a commit that origin does not (means someone pushed directly to mirror).
3. **If mirror has extra commits** — review them; if they are safe, cherry-pick to origin first, then push. If they are spurious, force-push from origin after confirming.
4. **Standard sync (no extra mirror commits):** `git push mirror main` (fast-forward).
5. **Force sync only if authorized:** `git push mirror main --force` — document reason in commit message.
6. **Verify after sync:** `git ls-remote origin main && git ls-remote mirror main` — must match.

**Recovery gate:** Both remotes at identical commit SHA.
