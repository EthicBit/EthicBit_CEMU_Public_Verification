# Regulatory Mapping Evidence — AEM-EVOLVE™ v1.1

**Type:** Regulatory mapping evidence (NOT regulatory approval)
**Version:** v1.1.0
**Scope:** Controlled-environment release — declared jurisdictions only

---

## What this is

AEM-EVOLVE™ v1.1 provides **regulatory mapping evidence** against selected AI governance frameworks.

Regulatory mapping evidence means: technical capabilities are mapped to framework requirements for transparency and traceability purposes.

## What this is NOT

- Not regulatory approval
- Not legal compliance
- Not conformity assessment
- Not external certification

## Frameworks mapped

| Framework | File | Jurisdictions |
|---|---|---|
| EU AI Act (2024/1689) | `EU_AI_ACT_MAPPING.json` | EU |
| NIST AI RMF 1.0 | `NIST_AI_RMF_MAPPING.json` | US |
| ISO/IEC 42001:2023 | `ISO_42001_MAPPING.json` | US, EU, UK, CO |

## How to verify

```bash
python3 demos/aem-evolve-multi-agent-api/tools/regulatory/regulatory_mapping_checker.py
```

Expected output:

```
REGULATORY_MAPPING_CHECK=PASS
```

Report generated at: `assurance/evolve-multi-agent/v1_1/regulatory_mapping_check_report.json`

## Supported claim

> AEM-EVOLVE™ v1.1 provides regulatory mapping evidence against selected governance frameworks, without claiming regulatory approval, certification, legal compliance, or conformity assessment.
