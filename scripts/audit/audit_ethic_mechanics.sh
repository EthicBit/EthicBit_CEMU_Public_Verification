#!/bin/bash
set -euo pipefail

REGISTRY_MANAGER="scripts/core/RegistryManager.py"
WRAPPER="scripts/core/ethic_mechanics_check.sh"

echo "=== ETHIC MECHANICS AUDIT (6 REAL SECTORS) ==="
echo "Sectors: CORE, JUSTICIA, FINANZAS, SECURITY, TECHNICAL, LEGAL"
echo

if [ ! -f "$REGISTRY_MANAGER" ] || [ ! -f "$WRAPPER" ]; then
    echo "ERROR: Required files not found"
    exit 2
fi

echo "=== 1. LOAD CHECK ==="
python3 "$REGISTRY_MANAGER" --rule-id "RULE-ETHIC-CORE-001-v1.0" --sector "CORE" --evidence-ok true >/dev/null
echo "OK: registries load"
echo

echo "=== 2. POSITIVE PATHS ==="
echo "-> CORE PASS"
"$WRAPPER" "RULE-ETHIC-CORE-001-v1.0" "CORE" "true"

echo "-> JUSTICIA PASS"
"$WRAPPER" "RULE-ETHIC-JUS-001-v3.1" "JUSTICIA" "true"

echo "-> FINANZAS PASS"
"$WRAPPER" "RULE-ETHIC-FIN-001-v3.0" "FINANZAS" "true"

echo "-> SECURITY PASS"
"$WRAPPER" "RULE-ETHIC-SEC-001-v2.0" "SECURITY" "true"

echo "-> TECHNICAL PASS"
"$WRAPPER" "RULE-ETHIC-TEC-001-v1.0" "TECHNICAL" "true"

echo "-> LEGAL PASS"
"$WRAPPER" "RULE-ETHIC-LEG-001-v2.0" "LEGAL" "true"
echo

echo "=== 3. FAIL_CLOSED PATHS ==="
for pair in \
  "CORE|RULE-ETHIC-CORE-001-v1.0" \
  "JUSTICIA|RULE-ETHIC-JUS-001-v3.1" \
  "FINANZAS|RULE-ETHIC-FIN-001-v3.0" \
  "SECURITY|RULE-ETHIC-SEC-001-v2.0" \
  "TECHNICAL|RULE-ETHIC-TEC-001-v1.0" \
  "LEGAL|RULE-ETHIC-LEG-001-v2.0"; do
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
echo "-> CORE fallback from LEGAL"
"$WRAPPER" "RULE-ETHIC-CORE-001-v1.0" "LEGAL" "true"

echo "-> REJECT expected"
if "$WRAPPER" "RULE-ETHIC-XYZ-999-v9.9" "JUSTICIA" "false"; then
  echo "ERROR: REJECT did not trigger"
  exit 1
else
  echo "OK: REJECT triggered"
fi
echo

echo "=============================================="
echo "ETHIC MECHANICS AUDIT: PASS"
echo "Validated sectors: CORE, JUSTICIA, FINANZAS, SECURITY, TECHNICAL, LEGAL"
echo "=============================================="
