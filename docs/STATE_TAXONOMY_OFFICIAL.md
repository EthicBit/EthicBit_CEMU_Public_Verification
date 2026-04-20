# Official State Taxonomy (v2.0.0)

## Purpose

This taxonomy removes ambiguity between:

- sovereign operational truth,
- canonical publication integrity,
- external assurance readiness,
- deployment authorization.

The system must not collapse these dimensions into one label.

## Axes

1. `operationalTruthStatus`
- Source: `officialOperationalStatusObserved`
- Typical values: `BLOCKED`, `DEGRADED`, `READY`, `FROZEN`

2. `canonicalIntegrityStatus`
- Source: `verified.packState`
- Typical values: `NOT_VERIFIED`, `ACTIVE_CANONICAL`

3. `externalAssuranceStatus`
- Source: `verified.externalAnchorState`
- Typical values: `NOT_VERIFIED`, `ANCHOR_HARDENING_ENABLED`, `ANCHOR_HARDENING_RECONCILED`

4. `deploymentAuthorizationStatus`
- Source: `verified.operationalReadiness`
- Allowed values:
  - `NOT_VERIFIED`
  - `READY_FOR_CONTROLLED_PRODUCTION_CANDIDATE`
  - `READY_FOR_CONTROLLED_PRODUCTION`
  - `CONTROLLED_PRODUCTION_ACTIVE`

## Promotion semantics

- `READY_FOR_CONTROLLED_PRODUCTION_CANDIDATE`:
  foundational controls pass, but controlled production authorization is still pending.

- `READY_FOR_CONTROLLED_PRODUCTION`:
  controlled production authorization is granted by canonical readiness checks.

- `CONTROLLED_PRODUCTION_ACTIVE`:
  controlled production is actively running under approved operational policy.

## Compatibility rule

Legacy artifacts may still contain candidate language.
Current canonical outputs should prefer this taxonomy and expose all four axes explicitly.

## Official closure references (2026-04-20)

Official documentary references for the current closure wave:

- `v2.2b-sovereign-preclose-20260419`
- `v2.2b-hybrid-claim-enforcement`
- `audit-freeze-20260419-hybrid-claim-enforcement`
- canonical merge commit on `main`: `2c0f086ed706c9998f8d66456fcb9b384a55ad29`

Freeze interpretation rule:

- `freezeActive=false` in a given operational-state artifact reflects runtime state at that timestamp.
- A formal freeze tag remains a valid immutable governance reference.
- Therefore, `freezeActive=false` and formal freeze-tag issuance are not contradictory.

## Where exposed

- `results/index.json` (`stateModel.*`)
- `results/GATE_REPORT.json` (`stateModel.*`)
- `artifacts/history/swarm/official_operational_status.json` (operational truth axis)
