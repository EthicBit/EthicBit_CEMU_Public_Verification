# RuntimeGuard L4 Baseline v10.0

Status: initial materialization

This document records the first explicit L4-oriented baseline for
`cemu/builders/runtime_guard.py`.

Present in tree:
- `cemu/builders/runtime_guard_l4_policy.json`
- `cemu/builders/runtime_guard.py` now references:
  - in-toto layout
  - SLSA provenance template
  - SLSA L4 policy
  - SLSA subject index
  - Sigstore policy baseline
  - regulatory policy baseline

Current interpretation:
This layer establishes an initial L4-oriented assurance gate model for RuntimeGuard.

It does not yet constitute:
- full L4 runtime enforcement,
- automatic cryptographic blocking,
- or hermetic runtime gate enforcement.
