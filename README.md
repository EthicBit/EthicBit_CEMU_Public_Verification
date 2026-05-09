# EthicBit_CEMU

[![L5 Full Chain Verification](https://github.com/EthicBit/EthicBit_CEMU/actions/workflows/l5_full_chain.yml/badge.svg)](https://github.com/EthicBit/EthicBit_CEMU/actions/workflows/l5_full_chain.yml)
[How to audit this repository](docs/AUDIT.md)

---

## Latest release: AEM-EVOLVE™ v1.1.0

**Tag:** `v1.1.0` — 2026-05-09
**Type:** Public controlled-environment assurance update

> AEM-EVOLVE™ v1.1 is regulator-mappable, governance-measurable, multi-anchor-verifiable, HITL-hardened, receipt-forgery-tested, and official-status-signed.

- [Public Status Bulletin (2026-05-09)](docs/STATUS_BULLETIN_PUBLIC_2026-05-09.md)
- [Whitepaper v1.1](docs/whitepapers/WHITEPAPER_V1_1_AEM_EVOLVE_GOVERNED_CHANGE_ASSURANCE.md)
- [GitHub Release v1.1.0](https://github.com/EthicBit/EthicBit_CEMU/releases/tag/v1.1.0)

### v1.1.0 verification

```bash
python3 demos/aem-evolve-multi-agent-api/tools/regulatory/regulatory_mapping_checker.py
python3 demos/aem-evolve-multi-agent-api/tools/metrics/governance_effectiveness_metrics.py
python3 demos/aem-evolve-multi-agent-api/tools/anchors/multi_anchor_verifier.py
python3 demos/aem-evolve-multi-agent-api/tools/hitl/HITL_signature_verifier.py
python3 demos/aem-evolve-multi-agent-api/adversarial_tests/test_receipt_forgery.py
python3 demos/aem-evolve-multi-agent-api/tools/status/official_status_signer.py
```

```
REGULATORY_MAPPING_CHECK=PASS
GOVERNANCE_EFFECTIVENESS_METRICS_STATUS=PASS
MULTI_ANCHOR_VERIFICATION=PASS
HITL_SIGNATURE_VERIFICATION=PASS_DEMO
RECEIPT_FORGERY_TESTS=PASS
OFFICIAL_STATUS_SIGNED=PASS
```

---

Canonical branch governance (effective 2026-04-18):

- Canonical operational and audit branch: `main`
- `master` is frozen and is not a delivery target
- All pull requests must target `main`

For contribution rules, see [CONTRIBUTING.md](CONTRIBUTING.md).

Release discipline references:

- [Release Grade Discipline Policy](docs/policies/RELEASE_GRADE_DISCIPLINE_POLICY.md)
- [Final Release Approval Checklist](docs/checks/FINAL_RELEASE_APPROVAL_CHECKLIST.md)
- [Release Notes - Hybrid Claim Enforcement Closure (2026-04-20)](docs/checks/RELEASE_NOTES_v2.2b_HYBRID_CLAIM_ENFORCEMENT_2026-04-20.md)
- [Public Status Bulletin (2026-04-20)](docs/STATUS_BULLETIN_PUBLIC_2026-04-20.md)
- [Public Status Bulletin (2026-05-09)](docs/STATUS_BULLETIN_PUBLIC_2026-05-09.md)
- [Independent Reproduction Challenge Pack](challenge/independent-reproduction/AEM_V1_1_INDEPENDENT_REPRODUCTION_CHALLENGE.md)

Final closure evidence snapshot:

- [Final Snapshot Manifest](results/final_snapshot/FINAL_SNAPSHOT_MANIFEST.json)
- [Final Snapshot Hashes](results/final_snapshot/artifact_hashes.sha256)
- [Final Audit Conclusion](FINAL_AUDIT_CONCLUSION.md)

v1.1.0 assurance artifacts:

- [Signed Official Status](assurance/evolve-multi-agent/v1_1/OFFICIAL_STATUS_SIGNED.json)
- [Hash Record v1.1](assurance/evolve-multi-agent/v1_1/V1_1_HASH_RECORD.txt)
- [Historical Baseline v10.1](docs/history/ETHICBIT_CEERV_CEMU_V10_1_MASTER_REPO_TREE.md)
- [AEM / AEM-EVOLVE™ Alignment](docs/architecture/AEM_AEM_EVOLVE_ALIGNMENT_WITH_ETHICBIT_CEERV_CEMU_V10_1.md)
- [Lingo and Claim Dictionary](docs/LINGO_AND_CLAIM_DICTIONARY.md)
