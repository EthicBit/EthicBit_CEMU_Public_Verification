# Semantic Versioning Policy — EthicBit/CEMU

**Version:** 1.0 | **Date:** 2026-05-18

---

## Version Format

`MAJOR.MINOR.PATCH[-PRERELEASE]`

Current version: `0.1.0` (pre-external-validation; first externally coherent baseline)

---

## Version Increment Rules

### MAJOR (X.0.0)

Increment MAJOR when:
- The constitutional controls regime changes in a backwards-incompatible way (e.g., new mandatory sector, removal of a sector gate)
- The claim boundary engine definition changes such that previously valid claims become invalid or vice versa
- The external validation state machine transitions to a new class (e.g., `HUMAN_ATTESTED` achieved — this marks v1.0.0)
- A breaking change to the in-toto statement schema or SBOM format

> `1.0.0` — reserved for first PRODUCTION_RELEASE class with external witness + human attestation.

### MINOR (0.X.0)

Increment MINOR when:
- A new in-toto attestation step is added to the chain
- A new assurance artifact type is introduced (new audit type, new validation criterion)
- A new anchor network is added to the canonical set
- A new validation criterion is resolved from PENDING_EXTERNAL to CONTROLLED_PASS
- Block-level remediations that materially expand the assurance posture (e.g., Blocks A-E)

### PATCH (0.0.X)

Increment PATCH when:
- Documentation updates, typo fixes, non-functional changes
- Dependency updates that don't change behavior
- Re-signing existing artifacts (no schema change)
- Bug fixes in scripts that don't affect assurance semantics
- Adding test cases without changing claim boundary logic

### Pre-release Labels

| Label | Meaning |
|-------|---------|
| `-alpha.N` | Experimental; not for external validation |
| `-beta.N` | Feature complete for the release class; external review invited |
| `-rc.N` | Release candidate; all gates pass; awaiting final human review |

---

## Version Locations

| File | Field | Update required on release |
|------|-------|---------------------------|
| `pyproject.toml` | `[project] version` | Yes |
| `assurance/slsa/l4/level4-policy.json` | `version` | On MINOR+ |
| `assurance/in-toto/attestation-index.json` | `version` | On schema change |
| `assurance/anchor/anchor-policy.json` | `version` | On policy change |

---

## Version History

| Version | Date | Notes |
|---------|------|-------|
| `0.1.0` | 2026-05-18 | First baseline post-remediation Blocks A-E. SLSA BASELINE_DOCUMENTED, in-toto KMS_SIGNED, SBOM signed, threat model, NIST RMF + ISO 42001 mappings. Pre-external-validation. |
