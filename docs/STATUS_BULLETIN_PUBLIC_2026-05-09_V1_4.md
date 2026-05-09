# EthicBit Public Status Bulletin

Date: 2026-05-09
Scope: AEM-EVOLVE™ v1.4.0 release — production hardening update

## Executive status

- Canonical branch: `main`
- Release tag: `v1.4.0`
- Official operational status: `READY`
- Internal closure status: `INTERNAL_CLOSED`
- External projection status: `EXTERNAL_LIVE_CONVERGED`
- Hybrid signature status: `SIGNED_HYBRID`
- Constitutional controls: `6/6 PASS` (`mustFailClosedTriggered=false`)
- Full-stack verification: `FULL_STACK_VERIFICATION=PASS (14/14)`
- LLM in governance path: `false`

## Release reference

- Release tag: `v1.4.0`
- Canonical merge commit on `main`: `e3eda3ce`
- PRs merged: #119 · #120 · #121 · #122 · #123 · #124 · #125
- GitHub release: `https://github.com/EthicBit/EthicBit_CEMU/releases/tag/v1.4.0`

## v1.4.0 verification results

```
FULL_STACK_VERIFICATION=PASS  (14/14)

  v1.1 stack (6/6):
  V1_1-REGULATORY-MAPPING      REGULATORY_MAPPING_CHECK=PASS
  V1_1-GOVERNANCE-METRICS      GOVERNANCE_EFFECTIVENESS_METRICS_STATUS=PASS
  V1_1-MULTI-ANCHOR            MULTI_ANCHOR_VERIFICATION=PASS
  V1_1-HITL-SIGNATURE          HITL_SIGNATURE_VERIFICATION=PASS_DEMO
  V1_1-RECEIPT-FORGERY         RECEIPT_FORGERY_TESTS=PASS
  V1_1-OFFICIAL-STATUS         OFFICIAL_STATUS_SIGNED=PASS

  v1.2 stack (2/2):
  V1_2-MECH-REASON-ENGINE      MECH_REASON_STATUS=PASS
  V1_2-MECH-REASON-VERIFY      MECH_REASON_VERIFICATION=PASS (10/10)

  v1.3 stack (4/4):
  V1_3-LLM-ADVISORY            LLM_ADVISORY_STATUS=PASS
  V1_3-MLKEM768                MLKEM768_STATUS=PASS (5/5)
  V1_3-HITL-QUORUM             HITL_QUORUM_VERIFICATION=PASS
  V1_3-POSTGRES-ADAPTER        POSTGRES_ADAPTER_VALIDATION=PASS (6/6)

  v1.4 stack (2/2):
  V1_4-SIGNING-PROVIDER        SIGNING_PROVIDER_VERIFICATION=PASS (8/8)
  V1_4-HITL-IDENTITY           HITL_IDENTITY_VERIFICATION=PASS (10/10)
```

Verification command:

```bash
python3 demos/aem-evolve-multi-agent-api/tools/reproduction/verify_all_v1_4.py
```

## What v1.4.0 adds

| PR | Gap closed |
|---|---|
| #119 | v1.4 roadmap |
| #120 | SigningProvider ABC — Ed25519 env + file providers, 8-check round-trip |
| #121 | HITL HMAC-SHA256 time-bounded token identity, TTL + registry enforcement |
| #122 | ML-KEM768 real library (mlkem FIPS 203) — corrected API |
| #123 | AsyncPostgresAdapter (asyncpg) + performance indexes |
| #124 | CI reproduction GitHub Actions workflow + Dockerfile.reproduction |
| #125 | Whitepaper v1.4 |

## v1.4.0 assurance artifacts

- `assurance/evolve-multi-agent/v1_4/signing_provider_report.json`
- `assurance/evolve-multi-agent/v1_4/hitl_identity_report.json`
- `assurance/evolve-multi-agent/v1_4/mlkem768_library_report.json`
- `assurance/evolve-multi-agent/v1_4/async_postgres_adapter_report.json`
- `assurance/evolve-multi-agent/v1_4/REPRODUCTION_REPORT.json`

## Source-of-truth evidence

- `demos/aem-evolve-multi-agent-api/tools/signing/verify_signing_provider.py`
- `demos/aem-evolve-multi-agent-api/tools/hitl/hitl_identity_verifier.py`
- `demos/aem-evolve-multi-agent-api/tools/crypto/mlkem768_setup_check.py`
- `demos/aem-evolve-multi-agent-api/tools/db/validate_async_postgres_adapter.py`
- `demos/aem-evolve-multi-agent-api/tools/reproduction/verify_all_v1_4.py`
- `docs/whitepapers/WHITEPAPER_V1_4_AEM_EVOLVE_PRODUCTION_HARDENING.md`
- `FINAL_AUDIT_CONCLUSION.md` (updated 2026-05-09)

## v1.4.0 claim

> AEM-EVOLVE™ v1.4 closes all production hardening gaps from the v1.3.0 audit: signing provider abstraction, HMAC-token HITL identity, real ML-KEM768 library, async PostgreSQL adapter, and CI-enforced reproduction workflow. Full-stack verification: 14/14 checks pass.

## What mixed audiences obtain

- **Big Tech / Model Labs / Agentic AI:**
  - 14-check full-stack verifier with CI gate; Dockerfile for container-based independent reproduction

- **Legal / Regulatory / Government:**
  - SigningProvider ABC enables HSM plug-in for production key custody; HITL token identity replaces demo-grade approver verification

- **Crypto / Financial / Cybersecurity:**
  - Real ML-KEM768 (FIPS 203) library confirmed operational (mode=mlkem); async PostgreSQL adapter for high-throughput governance event storage

- **Cross-economy executive audience:**
  - One-line decision signal: `v1.4.0 READY` — production-hardened, 14/14 verified, CI-gated, container-reproducible

## Governance controls

- Canonical branch: `main`
- Ruleset active: `constitutional-gate-main`
- Required status checks enforced: `production-distributed-ready-final` · `release-grade-discipline-gate`
- CI reproduction workflow: `aem-evolve-reproduction.yml` — runs on every push to main
- `master` remains frozen and non-operational for delivery

## Non-claims (transversal v1.4)

```
SigningProvider is not HSM-backed.
HSM integration requires an external implementation of the SigningProvider ABC.
HITL identity is not enterprise IAM.
HITL tokens are not production-grade without external IdP.
AsyncPostgresAdapter is not production-tested at scale.
ML-KEM768 is not independently audited.
CI reproduction is not external independent reproduction.
This release is not regulatory approval.
This release is not external certification.
```

## Cumulative stack baseline

```
EthicBit defines the standard.
CEERV defines offline verifiable evidence.
CEMU executes, seals, verifies, and governs the operational flow.
AEM-EVOLVE™ v1.1 adds governed change assurance.
AEM-EVOLVE™ v1.2 adds deterministic mechanical reasoning.
AEM-EVOLVE™ v1.3 closes five audit gaps and adds full-stack reproduction.
AEM-EVOLVE™ v1.4 closes production hardening gaps: signing abstraction,
                   HMAC-token HITL identity, real ML-KEM768 library,
                   async PostgreSQL, CI-enforced reproduction.
```
