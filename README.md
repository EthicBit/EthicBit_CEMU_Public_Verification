# EthicBit_CEMU

[![L5 Full Chain Verification](https://github.com/EthicBit/EthicBit_CEMU/actions/workflows/l5_full_chain.yml/badge.svg)](https://github.com/EthicBit/EthicBit_CEMU/actions/workflows/l5_full_chain.yml)
[How to audit this repository](docs/AUDIT.md)

---

## Full Technology Stack State — 2026-05-12

```
Constitutional regime:     EthicBit / CEMU v3.7.0+          ACTIVE
Artifact Assurance:        AEM v1.1                          ACTIVE
Governance Engine:         AEM-EVOLVE™                       ACTIVE
Evidence Baseline:         v2.0 PASS (14/14 gates, 140/140)  VERIFIED
Category Release:          AEM-EVOLVE v3.0                   RELEASED
AI-ME Gate Suite:          v3.1                              SPECIFICATION
Claim Boundary Engine:     Doctrine + Engine scaffold        ACTIVE
Fast Path:                 v1.0                              SPECIFICATION + SCAFFOLD
Triple Anchor:             Selected artifacts anchored       ACTIVE
Strong Closure:            v2.0 governance sign-off          ACTIVE
v4.0 External Validation:  Future roadmap                    ROADMAP
```

> The technology stack does not replace the EthicBit / CEMU constitutional-operational regime. It operationalizes it.

### Stack architecture

```
EthicBit / CEMU v3.7.0+  (Constitutional Regime)
  └─ AEM v1.1             (Artifact Assurance)
       └─ AEM-EVOLVE™     (Governance Assurance)
            └─ AI-ME Gates v3.1  (AI Evidence — Specification)
                 └─ Claim Boundary Engine™  (Claim Enforcement)
                      └─ Fast Path v1.0     (Pre-Execution Enforcement — Scaffold)
                           └─ Triple Anchor  (External Anchoring — selected receipts)
                                └─ Strong Closure  (Convergence Evaluation)
                                     └─ v4.0 External Validation  (Roadmap)
```

### Key documents (PR 0–J + K)

| Layer | Document |
|---|---|
| Constitutional Bridge | [docs/architecture/ETHICBIT_CONSTITUTIONAL_TECHNOLOGY_BRIDGE.md](docs/architecture/ETHICBIT_CONSTITUTIONAL_TECHNOLOGY_BRIDGE.md) |
| Technology Roadmap | [docs/strategy/ETHICBIT_AEM_EVOLVE_TECHNOLOGY_STATUS_AND_V3_V4_ROADMAP.md](docs/strategy/ETHICBIT_AEM_EVOLVE_TECHNOLOGY_STATUS_AND_V3_V4_ROADMAP.md) |
| AEM v1.1 Continuity | [docs/architecture/AEM_V1_1_ARTIFACT_ASSURANCE_CONTINUITY.md](docs/architecture/AEM_V1_1_ARTIFACT_ASSURANCE_CONTINUITY.md) |
| v3.0 Category Release | [docs/releases/AEM_EVOLVE_V3_0_CATEGORY_AND_DOCTRINE_RELEASE.md](docs/releases/AEM_EVOLVE_V3_0_CATEGORY_AND_DOCTRINE_RELEASE.md) |
| Whitepaper v3.0 | [docs/whitepapers/ETHICBIT_MECHANICAL_ETHICS_ASSURANCE_FOR_AI_V3_0.md](docs/whitepapers/ETHICBIT_MECHANICAL_ETHICS_ASSURANCE_FOR_AI_V3_0.md) |
| Claim Boundary Engine | [docs/strategy/CLAIM_BOUNDARY_ENGINE_ONE_PAGER.md](docs/strategy/CLAIM_BOUNDARY_ENGINE_ONE_PAGER.md) |
| AI-ME Gates Spec v3.1 | [docs/ai-me/AI_ME_GATES_SPEC_V3_1.md](docs/ai-me/AI_ME_GATES_SPEC_V3_1.md) |
| AI-ME Claim Boundary | [docs/ai-me/AI_ME_CLAIM_BOUNDARY_V3_1.md](docs/ai-me/AI_ME_CLAIM_BOUNDARY_V3_1.md) |
| High-Risk Taxonomy | [docs/ai-me/HIGH_RISK_OUTPUT_TAXONOMY_V3_1.md](docs/ai-me/HIGH_RISK_OUTPUT_TAXONOMY_V3_1.md) |
| AI-ME Evidence Schema | [docs/ai-me/AI_ME_EVIDENCE_SCHEMA_V3_1.json](docs/ai-me/AI_ME_EVIDENCE_SCHEMA_V3_1.json) |
| AI-ME Gate Matrix | [docs/ai-me/AI_ME_GATE_MATRIX_V3_1.json](docs/ai-me/AI_ME_GATE_MATRIX_V3_1.json) |
| Fast Path Spec | [docs/performance/FAST_PATH_DETERMINISTIC_PRE_EXECUTION_GATING.md](docs/performance/FAST_PATH_DETERMINISTIC_PRE_EXECUTION_GATING.md) |
| v4.0 Roadmap | [docs/strategy/AEM_EVOLVE_V4_0_EXTERNALIZED_MECHANICAL_ETHICS_ASSURANCE_ROADMAP.md](docs/strategy/AEM_EVOLVE_V4_0_EXTERNALIZED_MECHANICAL_ETHICS_ASSURANCE_ROADMAP.md) |
| Reproduction Kit v4.0 | [docs/reproduction/THIRD_PARTY_REPRODUCTION_KIT_V4_0.md](docs/reproduction/THIRD_PARTY_REPRODUCTION_KIT_V4_0.md) |
| Master Roadmap | [docs/strategy/ETHICBIT_ROADMAP_PR_0_J_PLUS_PR_K_FINAL.md](docs/strategy/ETHICBIT_ROADMAP_PR_0_J_PLUS_PR_K_FINAL.md) |

### AI-ME Gate Suite v3.1 — Specification Release

| Gate | Name | Domain | Fast Path |
|---|---|---|---|
| AI-ME-01 | Model Evaluation Evidence | Model | — |
| AI-ME-02 | Bias / Fairness Evidence | Fairness | — |
| AI-ME-03 | Explainability Artifact Evidence | Explainability | — |
| AI-ME-04 | Data Provenance & Lineage Evidence | Data | candidate |
| AI-ME-05 | Agent Trace Capture Evidence | Agent | candidate |
| AI-ME-06 | Tool-Call Governance Evidence | Tool | **HIGH** |
| AI-ME-07 | Memory Mutation Governance Evidence | Memory | candidate |
| AI-ME-08 | High-Risk Output Human Review Evidence | Human Oversight | **HIGH** |
| AI-ME-09 | Multi-Agent Coordination Governance Evidence | Multi-Agent | — |
| AI-ME-10 | AI Red-Team / Adversarial Robustness Evidence | Security | — |
| AI-ME-11 | Decision Logging & Appealability Evidence | Decision | — |
| AI-ME-12 | AI Claim Boundary Enforcement Evidence | Claim | **HIGH** |

Scaffold: `demos/aem-evolve-multi-agent-api/tools/ai_me/` (gates 01–04 + aggregator)

### Fast Path scaffold

```bash
# Verificar scaffold (sin evidencia real aún)
python3 -c "
import sys; sys.path.insert(0, '.')
from demos.aem_evolve_multi_agent_api.tools.fast_path.verify_fast_path import verify_scaffold
import json; print(json.dumps(verify_scaffold(), indent=2))
"
```

Scaffold: `demos/aem-evolve-multi-agent-api/tools/fast_path/`

### Final claim

EthicBit has versioned the constitutional, artifact-assurance, governance-assurance, AI evidence, claim-boundary, performance layer (Fast Path), and external validation roadmap for Mechanical Ethics Assurance for AI.

### Final non-claim

This does not claim completed AI-ME evidence execution, complete AI ethics coverage, universal production readiness, regulatory approval, external certification, third-party reproduction, HSM-backed custody, full-system sub-15 ms validation, or universal public anchoring unless separately evidenced.

---

## Latest release: AEM-EVOLVE™ v1.9.0 — OIDC Key Persistence · Materiality Parametrized · Postgres Live Test

**Tag:** `v1.9.0` — 2026-05-10
**Type:** Production hardening — OIDC key persistence (`oidc_key.pem`) · materiality parametrized (3 paths) · Postgres live verifier
**Full-stack verification:** `FULL_STACK_VERIFICATION=PASS (27/27)`

> AEM-EVOLVE™ v1.9 closes the three remaining technical gaps from the v1.8.0 audit: the OIDC RSA key pair is now file-based and stable across restarts, the governance graph accepts a `materiality_score` parameter covering all three paths (FAIL_CLOSED/SCOPE_LIMITED/PASS), and a Postgres live integration verifier is included (SKIP-safe when no DB available). Completes the v1.x hardening sequence.

- [Release Notes v1.9.0](demos/aem-evolve-multi-agent-api/RELEASE_NOTES_V1_9.md)

```bash
pip install cryptography mlkem asyncpg fastapi langgraph starlette httpx jose
python3 demos/aem-evolve-multi-agent-api/tools/reproduction/verify_all_v1_9.py
# FULL_STACK_VERIFICATION=PASS  (27/27)
```

---

## Previous release: AEM-EVOLVE™ v1.8.0 — Production Hardening: OIDC HITL · DB Adapter Switch · 109 Tests

**Tag:** `v1.8.0` — 2026-05-09
**Type:** Production hardening — OIDC dual-path HITL · PostgreSQL adapter switch · expanded pytest suite (109 tests)
**Full-stack verification:** `FULL_STACK_VERIFICATION=PASS (24/24)`

> AEM-EVOLVE™ v1.8 adds three production hardening measures: OIDC RS256 JWT support alongside HMAC in /approve (dual-path, backwards-compatible), an AEM_DB_ADAPTER env var for SQLite/PostgreSQL switching, and a 109-test pytest suite covering all governance controls.

- [Public Status Bulletin v1.8.0 (2026-05-09)](docs/STATUS_BULLETIN_PUBLIC_2026-05-09_V1_8.md)
- [Whitepaper v1.8](docs/whitepapers/WHITEPAPER_V1_8_AEM_EVOLVE_PRODUCTION_HARDENING.md)

```bash
pip install cryptography mlkem asyncpg fastapi langgraph starlette httpx jose
python3 demos/aem-evolve-multi-agent-api/tools/reproduction/verify_all_v1_8.py
# FULL_STACK_VERIFICATION=PASS  (24/24)
```

---

## Previous release: AEM-EVOLVE™ v1.7.0 — Read-Time Verification, Key Persistence, Anti-Replay

**Tag:** `v1.7.0` — 2026-05-10
**Type:** Security gap closure — read-time Ed25519 verification · file-based key persistence · HITL replay mitigation (409)
**Full-stack verification:** `FULL_STACK_VERIFICATION=PASS (21/21)`

> AEM-EVOLVE™ v1.7 closes the three critical gaps from the v1.6.0 post-release audit: artifacts are now verified at read time, the signing key persists across restarts, and HITL tokens are one-time-use enforced at the DB layer.

- [Public Status Bulletin v1.7.0 (2026-05-10)](docs/STATUS_BULLETIN_PUBLIC_2026-05-10_V1_7.md)
- [Whitepaper v1.7](docs/whitepapers/WHITEPAPER_V1_7_AEM_EVOLVE_READ_VERIFY_PERSIST_ANTIREPLAY.md)
- [GitHub Release v1.7.0](https://github.com/EthicBit/EthicBit_CEMU/releases/tag/v1.7.0)

```bash
pip install cryptography mlkem asyncpg fastapi langgraph starlette httpx
python3 demos/aem-evolve-multi-agent-api/tools/reproduction/verify_all_v1_7.py
# FULL_STACK_VERIFICATION=PASS  (21/21)
```

---

## AEM-EVOLVE™ v1.6.0 — Critical Gaps Closure

**Tag:** `v1.6.0` — 2026-05-09
**Type:** Critical gaps closure — signing wired · HITL token enforced · SQLiteAdapter activated · E2E integration test · CI updated
**Full-stack verification:** `FULL_STACK_VERIFICATION=PASS (18/18)`

> AEM-EVOLVE™ v1.6 closes all five critical gaps from the v1.5.0 audit: signing provider connected to API, HITL identity enforced in /approve, SQLiteAdapter activated, health endpoint fixed, and end-to-end integration test added.

- [Public Status Bulletin v1.6.0 (2026-05-09)](docs/STATUS_BULLETIN_PUBLIC_2026-05-09_V1_6.md)
- [Whitepaper v1.6](docs/whitepapers/WHITEPAPER_V1_6_AEM_EVOLVE_CRITICAL_GAPS_CLOSURE.md)
- [GitHub Release v1.6.0](https://github.com/EthicBit/EthicBit_CEMU/releases/tag/v1.6.0)

```bash
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
