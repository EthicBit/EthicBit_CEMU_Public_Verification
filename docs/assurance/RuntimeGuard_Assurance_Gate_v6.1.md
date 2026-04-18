# RuntimeGuard Assurance Gate v6.1

Status: initial materialization

This document records the first explicit assurance-gated extension of
`cemu/builders/runtime_guard.py`.

Present in tree:
- runtime guard now references:
  - in-toto layout
  - SLSA provenance template
  - Sigstore baseline policy
  - regulatory policy baseline

Current interpretation:
This layer establishes an initial assurance gate model for RuntimeGuard.

It does not yet constitute:
- full runtime enforcement,
- automatic blocking based on cryptographic validation,
- or L4-grade hermetic gate enforcement.
