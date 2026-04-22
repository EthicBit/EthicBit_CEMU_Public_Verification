#!/bin/bash
set -euo pipefail

REGISTRY_MANAGER="scripts/core/RegistryManager.py"
WRAPPER="scripts/core/ethic_mechanics_check_v22.sh"
GATE_SCRIPT="scripts/core/mechanical_ethics_gate.py"
GATE_OUTPUT="results/mechanical_ethics_gate.json"
GATE_REQUIRED_SECTORS="${ETHICBIT_ME_GATE_REQUIRED_SECTORS:-CORE,JUSTICIA,FINANZAS,SECURITY,TECHNICAL,LEGAL,REGULATORY}"

echo "=== ETHIC MECHANICS AUDIT (7 REAL SECTORS) ==="
echo "Sectors: CORE, JUSTICIA, FINANZAS, SECURITY, TECHNICAL, LEGAL, REGULATORY"
echo

if [ ! -f "$REGISTRY_MANAGER" ] || [ ! -f "$WRAPPER" ] || [ ! -f "$GATE_SCRIPT" ]; then
    echo "ERROR: Required files not found"
    exit 2
fi

echo "=== 1. LOAD CHECK ==="
"$WRAPPER" "RULE-ETHIC-CORE-001-v1.0" "CORE" "true" >/dev/null
echo "OK: registries load"
echo

echo "=== 2. POSITIVE PATHS ==="
for pair in \
  "CORE|RULE-ETHIC-CORE-001-v1.0" \
  "JUSTICIA|RULE-ETHIC-JUS-001-v3.1" \
  "FINANZAS|RULE-ETHIC-FIN-001-v3.0" \
  "SECURITY|RULE-ETHIC-SEC-001-v2.0" \
  "TECHNICAL|RULE-ETHIC-TEC-001-v1.0" \
  "LEGAL|RULE-ETHIC-LEG-001-v2.0" \
  "REGULATORY|RULE-ETHIC-REG-001-v2.1"; do
  IFS='|' read -r sector rule_id <<< "$pair"
  echo "-> $sector PASS"
  "$WRAPPER" "$rule_id" "$sector" "true"
done
echo

echo "=== 3. FAIL_CLOSED PATHS ==="
for pair in \
  "CORE|RULE-ETHIC-CORE-001-v1.0" \
  "JUSTICIA|RULE-ETHIC-JUS-001-v3.1" \
  "FINANZAS|RULE-ETHIC-FIN-001-v3.0" \
  "SECURITY|RULE-ETHIC-SEC-001-v2.0" \
  "TECHNICAL|RULE-ETHIC-TEC-001-v1.0" \
  "LEGAL|RULE-ETHIC-LEG-001-v2.0" \
  "REGULATORY|RULE-ETHIC-REG-001-v2.1"; do
  IFS='|' read -r sector rule_id <<< "$pair"
  echo "-> $sector FAIL_CLOSED expected"
  if "$WRAPPER" "$rule_id" "$sector" "false"; then
    echo "ERROR: $sector FAIL_CLOSED did not trigger"
    exit 1
  else
    echo "OK: $sector FAIL_CLOSED triggered"
  fi
done
echo

echo "=== 4. FALLBACK / REJECT ==="
echo "-> CORE fallback from REGULATORY"
"$WRAPPER" "RULE-ETHIC-CORE-001-v1.0" "REGULATORY" "true"

echo "-> REJECT expected"
if "$WRAPPER" "RULE-ETHIC-XYZ-999-v9.9" "JUSTICIA" "false"; then
  echo "ERROR: REJECT did not trigger"
  exit 1
else
  echo "OK: REJECT triggered"
fi
echo

echo "=== 5. CANONICAL MECHANICAL ETHICS GATE ==="
python3 "$GATE_SCRIPT" --output "$GATE_OUTPUT" --required-sectors "$GATE_REQUIRED_SECTORS"
python3 - <<'PY'
import json
from pathlib import Path

path = Path("results/mechanical_ethics_gate.json")
if not path.exists():
    raise SystemExit("mechanical_ethics_gate.json missing")

data = json.loads(path.read_text(encoding="utf-8"))
status = data.get("status")
mode = data.get("mode")
print(f"gate.status={status}")
print(f"gate.mode={mode}")
if status != "PASS":
    raise SystemExit("mechanical ethics gate status != PASS")
PY
echo

echo "=============================================="
echo "ETHIC MECHANICS AUDIT: PASS"
echo "Validated sectors: CORE, JUSTICIA, FINANZAS, SECURITY, TECHNICAL, LEGAL, REGULATORY"
echo "=============================================="
