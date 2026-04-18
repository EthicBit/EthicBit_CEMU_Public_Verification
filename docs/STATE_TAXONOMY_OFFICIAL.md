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
  - `READY_FOR_CONTROLLED_PRODUCTION`
  - `READY_FOR_CONTROLLED_PRODUCTION`
  - `CONTROLLED_PRODUCTION_ACTIVE`

## Promotion semantics

- `READY_FOR_CONTROLLED_PRODUCTION`:
  foundational controls pass, but controlled production authorization is still pending.

- `READY_FOR_CONTROLLED_PRODUCTION`:
  controlled production authorization is granted by canonical readiness checks.

- `CONTROLLED_PRODUCTION_ACTIVE`:
  controlled production is actively running under approved operational policy.

## Compatibility rule

Legacy artifacts may still contain candidate language.
Current canonical outputs should prefer this taxonomy and expose all four axes explicitly.

## Where exposed

- `results/index.json` (`stateModel.*`)
- `results/GATE_REPORT.json` (`stateModel.*`)
- `artifacts/history/swarm/official_operational_status.json` (operational truth axis)

