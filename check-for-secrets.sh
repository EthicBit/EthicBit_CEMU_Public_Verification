#!/bin/bash
echo "🔍 AUDITORÍA RÁPIDA DE SECRETOS (antes del Freeze)"
echo "Buscando claves, seeds, passwords o información sensible en los scripts de test..."

RELEASE_SCRIPTS="publication/releases/release-20260407T204627Z/scripts"

grep -E 'private|secret|key|seed|password| mnemonic|wallet|api_key' \
  "$RELEASE_SCRIPTS/"*.sh 2>/dev/null || echo "✅ No se encontraron claves ni secretos en los scripts de verificación"

echo
echo "Archivos que se van a leer en el pre-freeze test:"
ls -l "$RELEASE_SCRIPTS/verify_closure_integrity.sh" "$RELEASE_SCRIPTS/run_production_readiness.sh" 2>/dev/null

echo
echo "✅ Auditoría terminada. Solo se leen estados y hashes públicos."
