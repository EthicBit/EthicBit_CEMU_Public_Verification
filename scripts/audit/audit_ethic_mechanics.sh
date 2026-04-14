#!/bin/bash
set -euo pipefail

REGISTRY_MANAGER="scripts/core/RegistryManager.py"
WRAPPER="scripts/core/ethic_mechanics_check.sh"

echo "=== ETHIC MECHANICS AUDIT (4 REAL SECTORS) ==="
echo "Sectors: CORE, JUSTICIA, FINANZAS, SECURITY"
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
echo

echo "=== 3. FAIL_CLOSED PATHS ==="
echo "-> CORE FAIL_CLOSED expected"
if "$WRAPPER" "RULE-ETHIC-CORE-001-v1.0" "CORE" "false"; then
  echo "ERROR: CORE FAIL_CLOSED did not trigger"
  exit 1
else
  echo "OK: CORE FAIL_CLOSED triggered"
fi

echo "-> JUSTICIA FAIL_CLOSED expected"
if "$WRAPPER" "RULE-ETHIC-JUS-001-v3.1" "JUSTICIA" "false"; then
  echo "ERROR: JUSTICIA FAIL_CLOSED did not trigger"
  exit 1
else
  echo "OK: JUSTICIA FAIL_CLOSED triggered"
fi

echo "-> FINANZAS FAIL_CLOSED expected"
if "$WRAPPER" "RULE-ETHIC-FIN-001-v3.0" "FINANZAS" "false"; then
  echo "ERROR: FINANZAS FAIL_CLOSED did not trigger"
  exit 1
else
  echo "OK: FINANZAS FAIL_CLOSED triggered"
fi

echo "-> SECURITY FAIL_CLOSED expected"
if "$WRAPPER" "RULE-ETHIC-SEC-001-v2.0" "SECURITY" "false"; then
  echo "ERROR: SECURITY FAIL_CLOSED did not trigger"
  exit 1
else
  echo "OK: SECURITY FAIL_CLOSED triggered"
fi
echo

echo "=== 4. FALLBACK / REJECT ==="
echo "-> CORE fallback from SECURITY"
"$WRAPPER" "RULE-ETHIC-CORE-001-v1.0" "SECURITY" "true"

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
echo "Validated sectors: CORE, JUSTICIA, FINANZAS, SECURITY"
echo "=============================================="
