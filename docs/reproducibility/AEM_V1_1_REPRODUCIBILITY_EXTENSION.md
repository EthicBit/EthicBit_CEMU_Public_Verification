# AEM V1.1 Reproducibility Extension
## Toward Independently Reproduced Release Builds

System: EthicBit/CEMU  
Artifact: AEM V1.1 - Mechanical Ethical Agent  
Extension: AEM V1.1 Reproducibility Extension  
Current closure: `PUBLIC_REPRODUCIBLE_VERIFICATION_SUPPORT`  
Target closure: `INDEPENDENTLY_REPRODUCED_RELEASE_BUILD`

---

## 1. Purpose
The AEM V1.1 Reproducibility Extension defines a technical pathway toward independently reproduced release builds.

This extension does not modify the AEM V1.1 canonical artifact, the final Global Public Verification Registry, the Ethereum mainnet registry anchor, or the Supply-Chain Verification Extension. It adds clean-environment rebuild instructions, declared release subjects, expected hashes, comparison reporting, and independent attestation templates.

---

## 2. Scope Boundary
This extension does not currently claim:
- fully reproducible build;
- end-to-end deterministic rebuild;
- independently reproduced release build achieved;
- SLSA L4 fully proven;
- third-party reproduction completed;
- universal reproducibility across all environments.

This extension currently claims:
- a technical pathway toward independent reproduction;
- clean-environment rebuild instructions;
- declared release subjects;
- expected hash references;
- comparison report structure;
- independent reproduction attestation template;
- preparation toward `INDEPENDENTLY_REPRODUCED_RELEASE_BUILD`.

---

## 3. Relationship to AEM V1.1 Canonical Artifact
This extension does not mutate, replace, supersede, or reinterpret the AEM V1.1 canonical artifact.

The AEM V1.1 Global Public Verification Registry remains fixed. This extension adds a reproducibility layer intended to help independent reviewers rebuild declared release subjects from a public commit or release tag and compare resulting hashes against official expected hashes.

---

## 4. Relationship to the Supply-Chain Verification Extension
The Supply-Chain Verification Extension provides public reproducible verification support through SBOM artifacts, toolchain fingerprinting, signed provenance, signed release materials, manifest hashing, release verification, and Ethereum mainnet anchoring.

The Reproducibility Extension is distinct. It focuses on the next target level: independent reconstruction of declared release subjects.

```text
PUBLIC_REPRODUCIBLE_VERIFICATION_SUPPORT
= third parties can verify published artifacts.

INDEPENDENTLY_REPRODUCED_RELEASE_BUILD
= third parties can rebuild declared artifacts and demonstrate hash-equivalent reproduction.
```

---

## 5. Declared Release Subjects
Declared release subjects are listed in:

`assurance/reproducibility/declared_subjects.json`

Only declared subjects are within scope.

---

## 6. Expected Hashes
Expected hashes are listed in:

`assurance/reproducibility/expected_hashes.json`

Where applicable, JSON artifacts use deterministic canonicalization:

`json_sort_keys_no_whitespace_utf8`

Note: `canonical_sha256` and raw `file_sha256` may differ for the same JSON file, by design.

---

## 7. Clean-Environment Rebuild Model
The clean-environment model is documented in:

`docs/reproducibility/REPRODUCIBLE_BUILD_GUIDE.md`

Environment options included in this extension:
- Docker (`Dockerfile.reproducible`)
- Devcontainer (`.devcontainer/devcontainer.json`)
- Nix dev shell (`nix/flake.nix`)

---

## 8. Comparison Workflow
1. Checkout the public commit or release tag.
2. Prepare a clean environment.
3. Rebuild/resolve declared subjects.
4. Compute observed hashes.
5. Compare against expected hashes.
6. Generate comparison report.
7. Optionally complete independent reproduction report and third-party attestation.

---

## 9. Independent Reproduction Report
Template path:

`assurance/reproducibility/independent_reproduction_report.json`

Until completed by an independent reproducer, it remains non-attested.

---

## 10. Third-Party Attestation Template
Template path:

`assurance/reproducibility/third_party_reproduction_attestation_template.json`

This template does not constitute third-party verification until independently completed and signed.

---

## 11. Verification Commands
```bash
bash scripts/reproducibility/build_from_clean_environment.sh
python3 scripts/reproducibility/compare_reproducible_outputs.py
python3 scripts/reproducibility/generate_reproducibility_report.py
```

---

## 12. Current Publication Claim
Recommended public formulation:

AEM V1.1 Reproducibility Extension introduces a clean-environment pathway toward independently reproduced release builds, including declared subjects, expected hashes, comparison reporting, and independent attestation templates.

---

## 13. Claims Not Made
Do not claim:
- INDEPENDENTLY_REPRODUCED_RELEASE_BUILD achieved
- fully reproducible build achieved
- end-to-end deterministic rebuild proven
- SLSA L4 fully proven

---

## 14. Future Path
Future work may include:
- independent reproduction by a third-party verifier;
- signed independent reproduction report;
- hash-equivalent comparison against official release hashes;
- publication of independent attestation;
- Ethereum mainnet anchor of completed independent reproduction evidence;
- progression from `PUBLIC_REPRODUCIBLE_VERIFICATION_SUPPORT` toward `INDEPENDENTLY_REPRODUCED_RELEASE_BUILD`.

