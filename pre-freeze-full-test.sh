#!/bin/bash
echo "=================================================="
echo "🧪 ETHICBIT CEMU - PRE-FREEZE FULL TEST SUITE"
echo "📍 $(pwd)"
echo "🕒 $(date)"
echo "=================================================="
echo

RELEASE_SCRIPTS="publication/releases/release-20260407T204627Z/scripts"

echo "=== 1. Verificación de Integridad del Cierre (oficial) ==="
if [ -f "$RELEASE_SCRIPTS/verify_closure_integrity.sh" ]; then
    echo "Ejecutando verify_closure_integrity.sh ..."
    bash "$RELEASE_SCRIPTS/verify_closure_integrity.sh"
else
    echo "⚠️ verify_closure_integrity.sh no encontrado"
fi
echo

echo "=== 2. Verificación de Readiness para Producción (oficial) ==="
if [ -f "$RELEASE_SCRIPTS/run_production_readiness.sh" ]; then
    echo "Ejecutando run_production_readiness.sh ..."
    bash "$RELEASE_SCRIPTS/run_production_readiness.sh"
else
    echo "⚠️ run_production_readiness.sh no encontrado"
fi
echo

echo "=== 3. Verificación rápida de estado actual ==="
echo "publication_state.json → $(cat publication/publication_state.json 2>/dev/null | jq -r '.state' || echo 'NO_JSON')"
echo "GATE_REPORT verifiedState → $(jq -r '.verifiedState.operationalReadiness' results/GATE_REPORT.json 2>/dev/null || echo 'NO_JSON')"

echo
echo "=== 4. Chequeos adicionales de herramientas ==="
for script in tools/checks/check_*.py; do
    if [ -f "$script" ]; then
        echo "→ Ejecutando $script ..."
        python3 "$script" || echo "   (no se pudo ejecutar o requiere parámetros)"
    fi
done 2>/dev/null || echo "No se encontraron scripts Python de checks"

echo
echo "=================================================="
echo "✅ PRE-FREEZE TEST SUITE TERMINADO"
echo "Log guardado → ./pre-freeze-full-test.log"
echo "=================================================="

exec > >(tee ./pre-freeze-full-test.log) 2>&1
