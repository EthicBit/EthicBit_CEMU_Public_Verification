# AEM v1.1 Artifact Assurance Continuity

**Document type:** Artifact Assurance Continuity Declaration  
**Version:** 1.0  
**Status:** `ARTIFACT_ASSURANCE_ACTIVE`  
**Constitutional dependency:** EthicBit / CEMU v3.7.0+  
**Date:** 2026-05-12

---

## 1. Purpose

This document formalizes that AEM v1.1 remains the active Artifact Assurance layer for the EthicBit technology stack.

AEM v1.1 does not disappear in v3.x or v4.0. It is not replaced, superseded, or made redundant by any subsequent layer including AEM-EVOLVE™, AI-ME Gates, Fast Path, or Triple Anchor.

This document establishes the authoritative reference for AEM v1.1 continuity and its relationship with all subsequent technology layers in the PR 0–J + PR K roadmap.

---

## 2. Constitutional Position

AEM v1.1 is subordinate to the EthicBit / CEMU v3.7.0+ constitutional-operational regime and occupies the first functional layer in the architectural dependency order:

```
EthicBit / CEMU v3.7.0+ (Constitutional Regime)
  └─ AEM v1.1  ← Artifact Assurance Layer (THIS DOCUMENT)
       └─ AEM-EVOLVE™
            └─ AI-ME Gates
                 └─ Claim Boundary Engine™
                      └─ Fast Path
                           └─ Triple Anchor
                                └─ Strong Closure
                                     └─ v4.0 External Validation
```

No layer below AEM v1.1 can verify, validate, or replace it.

---

## 3. Architectural Position

AEM v1.1 is the Artifact Assurance Layer. Every subsequent layer depends on it to verify declared evidence artifacts before those artifacts can support claims.

**Dependency rule:**  
Where an artifact supports a governance claim, that artifact must be verifiable through AEM v1.1 before the related claim receives PASS or SCOPE_LIMITED.

---

## 4. AEM v1.1 Role

AEM v1.1 provides the following capabilities:

- **Artifact verification:** Verifies that a declared artifact exists, matches its declared hash, and is associated with its declared manifest.
- **Hash record maintenance:** Issues and maintains integrity references for verified artifacts.
- **Manifest management:** Supports execution manifests that enumerate and bind artifacts to governance events.
- **Verification receipts:** Issues verification receipts for artifacts that pass verification.
- **Fail-closed enforcement:** Blocks claims from reaching PASS where required artifacts are missing or unverified.
- **Anchor receipt reference:** Stores and references anchor receipts for artifacts anchored through Triple Anchor.
- **Canonical snapshot support:** Verifies canonical snapshots used by Fast Path as inheritance references.

---

## 5. Artifact Assurance Scope

AEM v1.1 covers the following artifact types:

- Execution manifests
- Evidence packages
- Model cards
- Fairness reports
- Explainability artifacts
- Data lineage graphs
- Agent trace reports
- Tool-call logs
- Memory mutation records
- HITL decisions
- Decision logs
- Claim boundary enforcement logs
- Canonical snapshots
- Fast Path snapshot references
- Final summaries
- Anchor receipts
- Verification receipts
- Governance sign-off records
- Audit records
- Hash records

---

## 6. Verification Model

AEM v1.1 applies the following verification model:

```
declare artifact
  → compute sha256 hash
    → compare against declared hash in manifest
      → if match: artifact_verified = true, issue verification receipt
      → if no match: artifact_verified = false, fail-closed if required
```

Where anchor receipts exist, AEM v1.1 also cross-references the declared artifact hash against the anchored hash.

AEM v1.1 does not claim artifact truth beyond hash and manifest consistency. It verifies structural integrity, not semantic correctness.

---

## 7. Fail-Closed Behavior

AEM v1.1 enforces fail-closed behavior where required artifacts are missing or unverified:

- If `artifact_assurance_required = true` and `artifact_verified = false`, the related claim cannot receive PASS.
- If a required artifact is missing from the manifest, the gate must emit FAIL_CLOSED or SCOPE_LIMITED.
- No downstream layer — including Fast Path — can upgrade a failed artifact assurance to PASS.

---

## 8. Relationship with AEM-EVOLVE™

AEM-EVOLVE™ is the Governance Assurance Layer. It depends on AEM v1.1 to verify evidence artifacts before governance outcomes can be issued.

- AEM-EVOLVE™ does not replace AEM v1.1.
- AEM-EVOLVE™ governance outcomes (PASS, SCOPE_LIMITED, FAIL_CLOSED) are only valid where underlying artifacts have been verified by AEM v1.1.
- AEM-EVOLVE™ v2.0 and v3.0 both depend on AEM v1.1 as their artifact foundation.

---

## 9. Relationship with AI-ME Gates

AI-ME Gates produce AI-specific evidence artifacts. These artifacts are subject to AEM v1.1 verification before they can support AI-ME evidence claims.

- AI-ME Gates do not replace AEM v1.1.
- Each AI-ME gate that produces evidence artifacts must declare those artifacts to AEM v1.1 for verification.
- AI-ME gate outcomes depend on artifact_assurance_status from AEM v1.1.
- Where `artifact_assurance_required = true` and `artifact_verified = false`, the AI-ME gate cannot emit PASS.

---

## 10. Relationship with Fast Path

Fast Path is a deterministic pre-execution enforcement layer. It may inherit or reference canonical snapshots and claim boundaries. Where Fast Path enforcement depends on a declared artifact, that artifact should be verified through AEM v1.1 before the related claim receives PASS or SCOPE_LIMITED.

Fast Path does not replace AEM v1.1.  
Fast Path PASS cannot upgrade a failed AEM v1.1 artifact assurance.  
Fast Path snapshot references should be verified through AEM v1.1 before use.

```
Fast Path may rely on artifacts, manifests, hashes, canonical snapshots or evidence
references verified or supported through AEM v1.1.

Where Fast Path enforcement depends on a declared artifact, that artifact should be
verified through AEM v1.1 before the related claim receives PASS or SCOPE_LIMITED.
```

---

## 11. Relationship with Triple Anchor

Triple Anchor anchors selected evidence states through external persistence targets. Anchor receipts reference artifacts previously verified by AEM v1.1.

- Triple Anchor does not replace AEM v1.1.
- Anchor receipts are issued after AEM v1.1 verification, not instead of it.
- Not every artifact is anchored. Where no anchor receipt exists, AEM v1.1 verification remains the integrity reference.

---

## 12. Supported Artifact Types

Full list of supported artifact types:

```
execution_manifest
evidence_package
model_card
fairness_report
explainability_artifact
data_lineage_graph
agent_trace_report
tool_call_log
memory_mutation_record
hitl_decision
decision_log
claim_boundary_enforcement_log
canonical_snapshot
fast_path_snapshot_reference
final_summary
anchor_receipt
verification_receipt
governance_signoff_record
audit_record
hash_record
sbom
supply_chain_artifact
reproduction_report
readiness_aggregate
```

---

## 13. Claims

AEM v1.1 remains the Artifact Assurance layer for verifying declared evidence artifacts used by AEM-EVOLVE™, AI-ME Gates, Fast Path and future workflows.

**Current evidence of AEM v1.1 activity:**
- `docs/anchors/AEM_V1_1_ARTIFACT_HASH_RECORD_2026-04-30.md`
- `docs/anchors/AEM_V1_1_GLOBAL_PUBLIC_VERIFICATION_REGISTRY_FINAL_ANCHOR_RECORD_2026-05-01.md`
- `docs/anchors/AEM_V1_1_MAINNET_ANCHOR_RECEIPT.json`
- `assurance/evolve-multi-agent/` — AEM-EVOLVE manifest, hash record, anchor receipt

---

## 14. Non-Claims

AEM v1.1 does not claim:

- Artifact truth beyond hash and manifest consistency
- Regulatory approval
- External certification
- Tamper-proof storage
- Universal reproducibility
- Public anchoring of every artifact
- Semantic correctness of artifact content
- That every artifact in the stack has been verified unless specific verification receipts exist

---

## 15. Roadmap Use in v3.1 and v4.0

**v3.1 (AI-ME Gate Suite):** AI-ME Gates produce evidence artifacts that require AEM v1.1 verification. The evidence schema (PR G) includes `artifact_assurance_required` and `artifact_assurance_status` fields explicitly tied to AEM v1.1.

**v4.0 (Externalized Validation):** v4.0 includes AEM v1.1 artifact reverification as a required component of third-party reproduction. External reviewers must verify artifact hashes and manifests through AEM v1.1 procedures before confirming evidence status.

---

## 16. Conclusion

AEM v1.1 is the active, persisting Artifact Assurance foundation of the EthicBit technology stack. Every layer above it depends on it. No layer replaces it.

The integrity of governance claims, AI-ME evidence, Fast Path enforcement, Triple Anchor receipts, and v4.0 external validation all rest on AEM v1.1 artifact verification. This continuity is non-negotiable under the EthicBit / CEMU constitutional-operational regime.

---

*AEM v1.1 Artifact Assurance Continuity v1.0 — EthicBit / CEMU v3.7.0+ — 2026-05-12*
