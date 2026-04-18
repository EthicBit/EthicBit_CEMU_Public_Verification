# Artifact Hierarchy and Naming

## Purpose
This document fixes the practical reading hierarchy of the main artifact names used across the repository.

## Core hierarchy
1. **artifact_manifest**
   - inventory or structured linking artifact
2. **bundle / case bundle**
   - consolidated artifact set for a case
3. **canonical root**
   - cryptographic fixing point for the case state
4. **Anchor Receipt**
   - external anchoring linkage artifact
5. **verification pack**
   - reproducibility / verification reinforcement artifact
6. **Formal Closure Certificate**
   - final closure certificate artifact

## CEERV initial layer
Inside `ceerv/`, the current initial equivalents are:
- `evidence_bundle_full.json`
- `certificate.json`
- `ACTA_MINIMA.json`
- `verification.json`
- `SSOT_MANIFEST_V1.json`

## Important distinction
These CEERV files currently represent **initial structural materialization**, not final universal hierarchy replacement for all legacy case artifacts.

## Naming rule
When possible:
- use the technical name,
- avoid switching between informal labels if that creates ambiguity,
- preserve distinction between:
  - closure artifact,
  - verification artifact,
  - anchoring artifact,
  - and bundle artifact.
