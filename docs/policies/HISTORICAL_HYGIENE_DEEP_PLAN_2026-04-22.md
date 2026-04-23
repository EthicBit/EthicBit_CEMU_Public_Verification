# Historical Hygiene Deep Plan (2026-04-22)

## Purpose

Establish a safe, auditable path to reduce historical repository bloat without weakening closure governance evidence.

This plan is explicitly split into:

- non-destructive preparation,
- controlled history rewrite window (optional),
- post-rewrite re-attestation.

## Current baseline (observed)

- Runtime/canonical closure artifacts are aligned and current.
- `.venv-mythril` and `*.pyc` were removed from active tracking in current branch state.
- Historical Git object store remains heavy and still requires deep hygiene if size reduction is a governance target.

## Execution phases

### Phase 0: Safety gates (mandatory)

1. Announce maintenance window and force-push impact.
2. Freeze merge activity during rewrite.
3. Create mirror backup before any rewrite.

### Phase 1: Non-destructive analysis

Use:

- `scripts/hygiene/historical_hygiene_deep_dry_run.sh`
- `git filter-repo --analyze`

Outputs required:

- top historical blob inventory,
- candidate path classes for rewrite,
- baseline object-store metrics.

### Phase 2: Controlled rewrite (optional, approved window only)

Recommended candidate classes:

- `.venv-mythril/**`
- `*.pyc`
- `**/__pycache__/**`

Important:

- execute only after backup and stakeholder approval,
- run in a dedicated maintenance branch or mirror clone first.

### Phase 3: Post-rewrite integrity and governance

1. Recompute closure artifacts and gate outputs.
2. Revalidate:
   - constitutional controls,
   - mechanical ethics gate,
   - official operational status,
   - hybrid signature verification.
3. Reissue freeze/release references if policy requires tag continuity.

### Phase 4: Publication and trust continuity

1. Publish migration note (history rewrite rationale + scope).
2. Preserve old hash references in an archival mapping document.
3. Confirm branch protections and required checks remain active.

## Decision rule

Proceed with deep rewrite only when:

- size reduction benefit is material,
- governance/audit continuity controls are ready,
- communication and rollback plans are approved.

Otherwise, keep current non-destructive hygiene and continue operational cadence.
