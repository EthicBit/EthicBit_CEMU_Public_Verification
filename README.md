# EthicBit_CEMU

[![L5 Full Chain Verification](https://github.com/EthicBit/EthicBit_CEMU/actions/workflows/l5_full_chain.yml/badge.svg)](https://github.com/EthicBit/EthicBit_CEMU/actions/workflows/l5_full_chain.yml)
[How to audit this repository](docs/AUDIT.md)

---

## Latest release: AEM-EVOLVE™ v1.6.0 — Critical Gaps Closure

**Tag:** `v1.6.0` — 2026-05-09
**Type:** Critical gaps closure — signing wired · HITL token enforced · SQLiteAdapter activated · E2E integration test · CI updated
**Full-stack verification:** `FULL_STACK_VERIFICATION=PASS (18/18)`

> AEM-EVOLVE™ v1.6 closes all five critical gaps from the v1.5.0 audit: signing provider connected to API, HITL identity enforced in /approve, SQLiteAdapter activated, health endpoint fixed, and end-to-end integration test added.

- [Public Status Bulletin v1.6.0 (2026-05-09)](docs/STATUS_BULLETIN_PUBLIC_2026-05-09_V1_6.md)
- [Whitepaper v1.6](docs/whitepapers/WHITEPAPER_V1_6_AEM_EVOLVE_CRITICAL_GAPS_CLOSURE.md)
- [GitHub Release v1.6.0](https://github.com/EthicBit/EthicBit_CEMU/releases/tag/v1.6.0)

```bash
pip install cryptography mlkem asyncpg fastapi langgraph starlette httpx
python3 demos/aem-evolve-multi-agent-api/tools/reproduction/verify_all_v1_6.py
# FULL_STACK_VERIFICATION=PASS  (18/18)
```

---

## Previous release: AEM-EVOLVE™ v1.5.0 — Enterprise Hardening

**Tag:** `v1.5.0` — 2026-05-09
**Type:** Enterprise hardening — PKCS#11/KMS stubs · OIDC JWT HITL · dependency validation · async concurrency · pgbouncer · v1.4 challenge
**Full-stack verification:** `FULL_STACK_VERIFICATION=PASS (16/16)`

> AEM-EVOLVE™ v1.5 closes all enterprise hardening gaps from the v1.4.0 audit.

- [Public Status Bulletin v1.5.0 (2026-05-09)](docs/STATUS_BULLETIN_PUBLIC_2026-05-09_V1_5.md)
- [Whitepaper v1.5](docs/whitepapers/WHITEPAPER_V1_5_AEM_EVOLVE_ENTERPRISE_HARDENING.md)
- [GitHub Release v1.5.0](https://github.com/EthicBit/EthicBit_CEMU/releases/tag/v1.5.0)

```bash
python3 demos/aem-evolve-multi-agent-api/tools/reproduction/verify_all_v1_5.py
# FULL_STACK_VERIFICATION=PASS  (16/16)
```

---

## Previous release: AEM-EVOLVE™ v1.4.0 — Production Hardening

**Tag:** `v1.4.0` — 2026-05-09
**Type:** Production hardening — signing abstraction · HMAC-token HITL identity · ML-KEM768 real library · async PostgreSQL · CI reproduction
**Full-stack verification:** `FULL_STACK_VERIFICATION=PASS (14/14)`

> AEM-EVOLVE™ v1.4 closes all production hardening gaps from the v1.3.0 audit: signing provider abstraction, HMAC-token HITL identity, real ML-KEM768 library, async PostgreSQL adapter, and CI-enforced reproduction workflow.

- [Public Status Bulletin v1.4.0 (2026-05-09)](docs/STATUS_BULLETIN_PUBLIC_2026-05-09_V1_4.md)
- [Whitepaper v1.4](docs/whitepapers/WHITEPAPER_V1_4_AEM_EVOLVE_PRODUCTION_HARDENING.md)
- [GitHub Release v1.4.0](https://github.com/EthicBit/EthicBit_CEMU/releases/tag/v1.4.0)

### v1.4.0 verification

```bash
pip install cryptography mlkem asyncpg
python3 demos/aem-evolve-multi-agent-api/tools/reproduction/verify_all_v1_4.py
```

```
FULL_STACK_VERIFICATION=PASS  (14/14)
  v1.1: 6/6  ·  v1.2: 2/2  ·  v1.3: 4/4  ·  v1.4: 2/2
```

v1.4.0 assurance artifacts:

- [Signing Provider Report](assurance/evolve-multi-agent/v1_4/signing_provider_report.json)
- [HITL Identity Report](assurance/evolve-multi-agent/v1_4/hitl_identity_report.json)
- [ML-KEM768 Library Report](assurance/evolve-multi-agent/v1_4/mlkem768_library_report.json)
- [Async PostgreSQL Adapter Report](assurance/evolve-multi-agent/v1_4/async_postgres_adapter_report.json)
- [Reproduction Report](assurance/evolve-multi-agent/v1_4/REPRODUCTION_REPORT.json)

---

## Previous release: AEM-EVOLVE™ v1.3.0 — Gaps Closure

**Tag:** `v1.3.0` — 2026-05-09
**Type:** Gaps closure — LLM adapter · ML-KEM768 · HITL quorum · PostgreSQL · reproduction toolkit
**Full-stack verification:** `FULL_STACK_VERIFICATION=PASS (12/12)`

> AEM-EVOLVE™ v1.3 closes the five gaps identified in the v1.2.0 audit: LLM advisory adapter, ML-KEM768 KEM runtime, HITL quorum model, PostgreSQL adapter activation, and independent reproduction toolkit.

- [Public Status Bulletin v1.3.0 (2026-05-09)](docs/STATUS_BULLETIN_PUBLIC_2026-05-09_V1_3.md)
- [Whitepaper v1.3](docs/whitepapers/WHITEPAPER_V1_3_AEM_EVOLVE_GAPS_CLOSURE.md)
- [GitHub Release v1.3.0](https://github.com/EthicBit/EthicBit_CEMU/releases/tag/v1.3.0)

---

## Previous release: AEM-EVOLVE™ v1.2.0 — Mechanical Reasoning Layer

**Tag:** `v1.2.0` — 2026-05-09

> AEM-EVOLVE™ v1.2 introduces MECH-REASON™, a deterministic reasoning engine for policy-bound, evidence-based governance recommendations.

- [Public Status Bulletin v1.2.0 (2026-05-09)](docs/STATUS_BULLETIN_PUBLIC_2026-05-09_V1_2.md)
- [Whitepaper v1.2](docs/whitepapers/WHITEPAPER_V1_2_AEM_EVOLVE_MECHANICAL_REASONING_LAYER.md)
- [GitHub Release v1.2.0](https://github.com/EthicBit/EthicBit_CEMU/releases/tag/v1.2.0)

---

## Previous release: AEM-EVOLVE™ v1.1.0

**Tag:** `v1.1.0` — 2026-05-09

> AEM-EVOLVE™ v1.1 is regulator-mappable, governance-measurable, multi-anchor-verifiable, HITL-hardened, receipt-forgery-tested, and official-status-signed.

- [Public Status Bulletin (2026-05-09)](docs/STATUS_BULLETIN_PUBLIC_2026-05-09.md)
- [Whitepaper v1.1](docs/whitepapers/WHITEPAPER_V1_1_AEM_EVOLVE_GOVERNED_CHANGE_ASSURANCE.md)
- [GitHub Release v1.1.0](https://github.com/EthicBit/EthicBit_CEMU/releases/tag/v1.1.0)

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
- [Public Status Bulletin v1.1.0 (2026-05-09)](docs/STATUS_BULLETIN_PUBLIC_2026-05-09.md)
- [Public Status Bulletin v1.2.0 (2026-05-09)](docs/STATUS_BULLETIN_PUBLIC_2026-05-09_V1_2.md)
- [Public Status Bulletin v1.3.0 (2026-05-09)](docs/STATUS_BULLETIN_PUBLIC_2026-05-09_V1_3.md)
- [Public Status Bulletin v1.4.0 (2026-05-09)](docs/STATUS_BULLETIN_PUBLIC_2026-05-09_V1_4.md)
- [Independent Reproduction Challenge v1.1](challenge/independent-reproduction/AEM_V1_1_INDEPENDENT_REPRODUCTION_CHALLENGE.md)
- [Independent Reproduction Challenge v1.3](challenge/independent-reproduction/AEM_V1_3_INDEPENDENT_REPRODUCTION_CHALLENGE.md)

Final closure evidence snapshot:

- [Final Snapshot Manifest](results/final_snapshot/FINAL_SNAPSHOT_MANIFEST.json)
- [Final Snapshot Hashes](results/final_snapshot/artifact_hashes.sha256)
- [Final Audit Conclusion](FINAL_AUDIT_CONCLUSION.md)

v1.2.0 assurance artifacts:

- [MECH_REASON_REPORT](assurance/evolve-multi-agent/v1_2/MECH_REASON_REPORT.json)
- [MECH_REASON_VERIFICATION_REPORT](assurance/evolve-multi-agent/v1_2/MECH_REASON_VERIFICATION_REPORT.json)
- [Hash Record v1.2](assurance/evolve-multi-agent/v1_2/V1_2_HASH_RECORD.txt)

v1.1.0 assurance artifacts:

- [Signed Official Status](assurance/evolve-multi-agent/v1_1/OFFICIAL_STATUS_SIGNED.json)
- [Hash Record v1.1](assurance/evolve-multi-agent/v1_1/V1_1_HASH_RECORD.txt)
- [Historical Baseline v10.1](docs/history/ETHICBIT_CEERV_CEMU_V10_1_MASTER_REPO_TREE.md)
- [AEM / AEM-EVOLVE™ Alignment](docs/architecture/AEM_AEM_EVOLVE_ALIGNMENT_WITH_ETHICBIT_CEERV_CEMU_V10_1.md)
- [Lingo and Claim Dictionary](docs/LINGO_AND_CLAIM_DICTIONARY.md)
