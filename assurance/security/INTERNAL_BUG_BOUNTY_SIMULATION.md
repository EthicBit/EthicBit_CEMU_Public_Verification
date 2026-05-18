# Internal Bug Bounty Simulation — EthicBit/CEMU v4.0

**Version:** 1.0 | **Date:** 2026-05-18  
**Status:** SIMULATION_COMPLETE — no real bounty program active  
**Purpose:** Exercise the vulnerability intake and triage process before opening a public program

---

## Scope

| In scope | Out of scope |
|----------|-------------|
| Claim boundary bypass (CBE logic) | Third-party npm packages |
| KMS signing key exposure via committed files | Node.js runtime vulnerabilities |
| in-toto chain integrity (signature bypass) | Arweave/AO network-level attacks |
| SLSA build workflow tampering | Social engineering attacks |
| Automated elevation of human_attestation_status | DDoS against anchor networks |
| AWS ID leakage in public-facing artifacts | Physical infrastructure |

---

## Simulated Reports and Outcomes

### SIM-001 — Claim Boundary Bypass via Missing Case

**Reporter (simulated):** Internal red-team  
**Finding:** If a new claim is added to `claim_boundary_regression_cases.json` with `expected_decision: "ALLOWED"` instead of `"BLOCKED"`, the `run_claim_red_team.py` runner would output `FAIL_CLOSED` — not silently pass.  
**Severity:** HIGH (if the case file were modified to weaken a block)  
**Actual behavior:** `evaluate_case()` returns `FAIL_CLOSED` for any `expected_decision != "BLOCKED"`. Hypothesis I-M meta-test catches this.  
**Resolution:** Not a vulnerability in the current implementation. Documented as invariant I-M in `tests/test_claim_boundary_properties.py`.  
**Status:** CLOSED_NOT_VULNERABLE

---

### SIM-002 — AWS Key ID Exposure in Commit

**Reporter (simulated):** Internal security review  
**Finding:** KMS key UUID `977feb8e-...` appears in `assurance/in-toto/attestations/*.statement.json` under `signedBy`.  
**Severity:** MEDIUM (key ID alone does not grant signing access; IAM credentials required)  
**Actual behavior:** Key ID in `signedBy` is intentional for verification — it identifies which key to use for `kms:Verify`. Not a secret.  
**Resolution:** Distinction documented: key ID ≠ secret. Key alias used in public-facing policy files. `check_no_aws_ids.py` pre-commit hook exempts `assurance/in-toto/` from key UUID check.  
**Status:** CLOSED_ACCEPTED_RISK — intentional transparency

---

### SIM-003 — SLSA Build Workflow `workflow_dispatch` Allows Unsigned Build

**Reporter (simulated):** External reviewer  
**Finding:** `slsa-build.yml` has `workflow_dispatch` trigger, allowing a build to be manually triggered by any user with Actions write access — potentially producing a build manifest not tied to a PR merge.  
**Severity:** MEDIUM  
**Resolution:** `workflow_dispatch` builds produce a manifest with the triggering commit SHA. The manifest is uploaded as an artifact and not automatically merged into main. Downstream signing in `slsa_hybrid_attest.yml` requires the same commit SHA. Manual triggers are auditable in GitHub Actions logs.  
**Residual risk:** A user with write access could trigger a build on an attacker-controlled branch. Mitigated by restricting Actions write access to maintainers.  
**Status:** OPEN_ACCEPTED_RISK — mitigated by access control; document for Block E follow-up

---

### SIM-004 — in-toto Statements Not in DSSE Envelope

**Reporter (simulated):** Supply chain security researcher  
**Finding:** EthicBit in-toto statements use a custom `ETHICBIT_IN_TOTO_STATEMENT_V1` envelope rather than the canonical DSSE (Dead Simple Signing Envelope) format required by in-toto v1.0. Third-party `in-toto-verify` tooling cannot verify them directly.  
**Severity:** MEDIUM  
**Resolution:** Acknowledged gap. Documented in `docs/assurance/FRAMEWORK_COMPARATIVE_ANALYSIS.md` (in-toto gap table). KMS-based ECDSA_SHA_256 signature is cryptographically sound; the gap is format compatibility, not signature security. Migration to DSSE envelope is a future improvement.  
**Status:** OPEN_KNOWN_GAP — tracked for post-external-validation remediation

---

### SIM-005 — Anchor Receipt Files Not Cryptographically Linked to Commit

**Reporter (simulated):** Auditor  
**Finding:** `anchor_txids_real.json` contains TXIDs but no SHA256 of the anchor receipt itself or the git commit that triggered the anchor. An attacker could swap TXIDs without a visible signature chain.  
**Severity:** LOW  
**Resolution:** Anchor receipts are in git history — any modification creates a visible commit. The anchor scripts hash the artifacts before anchoring (KZG blob contains the artifact hashes). The root hash in `anchor_txids_real.json` (`f7e7b527...`) covers the anchored content.  
**Status:** CLOSED_MITIGATED — git history + content hashing provide integrity

---

## Triage Process (for future real reports)

1. **Intake** — report received via designated channel; assigned `SIM-NNN` or `BUG-NNN` ID.
2. **Initial triage** — within 24h: confirm scope, initial severity rating.
3. **Reproduction** — reproduce on clean checkout; confirm or deny finding.
4. **Assessment** — is it a vulnerability in EthicBit/CEMU logic, or a known accepted risk?
5. **Resolution options:**
   - `CLOSED_NOT_VULNERABLE` — behavior is correct
   - `CLOSED_ACCEPTED_RISK` — acknowledged, documented, mitigated sufficiently
   - `OPEN_KNOWN_GAP` — tracked for future remediation
   - `PATCHED` — fixed in a commit; regression test added
6. **Disclosure** — after resolution, add to this document.

---

## Findings Summary

| ID | Severity | Status |
|----|----------|--------|
| SIM-001 | HIGH | CLOSED_NOT_VULNERABLE |
| SIM-002 | MEDIUM | CLOSED_ACCEPTED_RISK |
| SIM-003 | MEDIUM | OPEN_ACCEPTED_RISK |
| SIM-004 | MEDIUM | OPEN_KNOWN_GAP |
| SIM-005 | LOW | CLOSED_MITIGATED |

**0 unmitigated HIGH findings. 2 OPEN items documented for future remediation.**
