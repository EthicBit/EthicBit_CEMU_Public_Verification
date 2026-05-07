#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

echo "=== AEM-EVOLVE CONTROLLED TECHNICAL DEMO ==="
python3 scripts/evolve/verify_evolution_receipt.py
