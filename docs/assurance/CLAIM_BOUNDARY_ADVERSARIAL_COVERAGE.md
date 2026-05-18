# Claim Boundary — Adversarial Coverage

**Version:** 1.0  
**Date:** 2026-05-18  
**Status:** ACTIVE  

## Purpose

Documents the adversarial coverage strategy for the EthicBit/CEMU Claim Boundary Engine (CBE).
The CBE prevents overclaims — assertions unsupported by present evidence — from propagating into
public-facing materials, CI outputs, or external validation packages.

This document covers two complementary layers: the deterministic red-team regression corpus and
the property-based tests introduced in Block C.

---

## Coverage Layers

### Layer 1 — Deterministic Red-Team Corpus

File: `tools/external_validation/claim_red_team/claim_boundary_regression_cases.json`

14 curated cases (CBRT-001 through CBRT-014) each attempting a specific unsupported overclaim.
Every case must evaluate to `BLOCKED`. Any deviation triggers `FAIL_CLOSED` at the report level.

| Case | Attempted Overclaim |
|------|-------------------|
| CBRT-001 | Regulatory approval |
| CBRT-002 | Universal production readiness |
| CBRT-003 | Cybersecurity certification |
| CBRT-004 | Financial advice / compliance |
| CBRT-005 | Clinical/diagnostic approval |
| CBRT-006 | Tamper-proof storage |
| CBRT-007 | Universal public anchoring |
| CBRT-008 | Full-system sub-15 ms latency |
| CBRT-009 | Third-party reproduction completed |
| CBRT-010 | External certification |
| CBRT-011 | SLSA L4 fully achieved |
| CBRT-012 | SLSA L4 certified |
| CBRT-013 | Production supply-chain certified |
| CBRT-014 | Externally verified in-toto chain |

### Layer 2 — Property-Based Tests (Hypothesis)

File: `tests/test_claim_boundary_properties.py`

Five structural invariants + one meta-invariant, each exercised with `max_examples=500` (I-M: 200):

| ID | Invariant | What Hypothesis generates |
|----|-----------|--------------------------|
| I-1 | `expected_decision=BLOCKED` → result `BLOCKED` | Arbitrary valid cases |
| I-2 | Missing `permitted_alternative` → `FAIL_CLOSED` | Valid cases with empty alternative |
| I-3 | Missing `required_external_condition` → `FAIL_CLOSED` | Valid cases with empty condition |
| I-4 | `expected_decision` ∉ `{BLOCKED}` → `FAIL_CLOSED` | Arbitrary non-BLOCKED decisions |
| I-5 | All 13 `non_claims` fields = `False` | Fixed (runs against live corpus) |
| I-M | Injecting a forbidden-decision case → report not `PASS` | Forbidden-decision cases appended to corpus |

---

## Non-Claims Boundary

The following are structurally blocked and verified by I-5 on every CI run:

- `completed_external_claim_review` = false  
- `completed_external_validation` = false  
- `external_certification` = false  
- `regulatory_approval` = false  
- `cybersecurity_certification` = false  
- `financial_advice` = false  
- `clinical_or_diagnostic_readiness` = false  
- `universal_production_readiness` = false  
- `third_party_reproduction_completed` = false  
- `slsa_l4_fully_achieved` = false  
- `slsa_l4_certification` = false  
- `production_supply_chain_certification` = false  
- `externally_verified_in_toto_chain` = false  

---

## Gaps and Limitations

- Property tests exercise `evaluate_case` and `build_report` logic only; they do not test
  the full report-verification pipeline (`verify_claim_red_team_report.py`).
- Hypothesis generates structurally valid inputs; it does not generate semantically misleading
  permitted_alternative strings that might pass structural checks but misrepresent scope.
- External validation state (`human_attestation_status`) is validated as a fixed invariant
  (`HUMAN_ATTESTATION_PENDING`); elevation to `HUMAN_ATTESTED` requires out-of-band human sign-off.

---

## CI Integration

Workflow: `.github/workflows/claim-boundary-property-tests.yml`

Runs on every push to `main` and on every pull request. Failure blocks merge.
Hypothesis database (`tests/.hypothesis/`) is cached across runs to preserve found counter-examples.
