#!/bin/bash
set -euo pipefail

RULE_ID="${1:-}"
SECTOR="${2:-CORE}"
EVIDENCE_OK="${3:-true}"

python3 scripts/core/RegistryManager.py --rule-id "$RULE_ID" --sector "$SECTOR" --evidence-ok "$EVIDENCE_OK"
