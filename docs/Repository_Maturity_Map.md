# Repository Maturity Map

## Purpose
This document maps the maturity level of the main layers of the repository.

## Maturity legend
- **MATERIALIZED**: present with real files and usable content
- **INITIAL**: present but still early-stage / baseline / scaffold-backed
- **DOCUMENTED**: described clearly but not fully expressed structurally
- **PENDING**: not yet materially present

| Layer | Current status | Notes |
|---|---|---|
| Constitutional baseline | DOCUMENTED | ETHICBIT / CEMU v3.7.0+ governs interpretation |
| case_003 remediated core | MATERIALIZED | canonical artifacts, closure state, approval, certificate present |
| CEERV structural layer | INITIAL | explicit sub-tree present and populated |
| CEMU structural layer | INITIAL | explicit sub-tree present and populated in core/builders |
| Assurance baseline | INITIAL | workflows and assurance scaffolds present |
| Public executive layer | DOCUMENTED / ACOTADO | not confirmed as populated in active tree |
| Full CEERV compliance | PENDING | not yet complete |
| Full CEMU capsule completeness | PENDING | outputs/templates still mostly empty |
| Full SLSA L3 / in-toto / Sigstore enforcement | PENDING | baseline only |

## Reading rule
No layer should be described as complete merely because a directory exists.
SLSA_L4_FULL: IN_PROGRESS
