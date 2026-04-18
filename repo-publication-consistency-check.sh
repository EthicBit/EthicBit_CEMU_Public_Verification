#!/bin/bash
echo "=================================================="
echo "🔍 ETHICBIT CEMU - ANÁLISIS DE PUBLICACIÓN + CONSISTENCIA"
echo "📍 $(pwd)"
echo "🕒 $(date)"
echo "=================================================="
echo

RELEASE_DIR="publication/releases/release-20260407T204627Z"

echo "=== 1. Detalle de la última publicación ==="
ls -la "$RELEASE_DIR"
echo
ls -la "$RELEASE_DIR/artifacts"

echo
echo "=== 2. publication_state.json ==="
cat publication/publication_state.json 2>/dev/null || echo "⚠️ No encontrado"

echo
echo "=== 3. Manifest principal de la release ==="
cat "$RELEASE_DIR/artifacts/artifact_manifest.json" 2>/dev/null | jq '.' || cat "$RELEASE_DIR/artifacts/artifact_manifest.json" 2>/dev/null || echo "⚠️ No se pudo leer"

echo
echo "=== 4. Certificado formal de cierre ==="
cat "$RELEASE_DIR/artifacts/formal_closure_certificate_multicapa_v1_0.json" 2>/dev/null | jq '.' || echo "⚠️ No se pudo leer el certificado"

echo
echo "=== 5. Hashes del release (comparación) ==="
cat "$RELEASE_DIR/artifacts/ethicbit_closure_artifacts_hashes.json" 2>/dev/null | jq '.' || echo "⚠️ No se pudo leer hashes"

echo
echo "=== 6. Consistencia con Master State Document ==="
echo "Buscando referencias a la release en el Master State..."
grep -n "20260407" docs/technical/EthicBit_CEMU_v3_7_0_plus_Master_State_Document_v1_3.md || echo "No se encontró fecha exacta de release"
grep -n "release-20260407" docs/technical/EthicBit_CEMU_v3_7_0_plus_Master_State_Document_v1_3.md || echo "No se encontró ID de release"

echo
echo "=== 7. Scripts de verificación de la publicación ==="
ls -la "$RELEASE_DIR/scripts"

echo
echo "=================================================="
echo "✅ ANÁLISIS DE PUBLICACIÓN TERMINADO"
echo "Log guardado → ./repo-publication-consistency.log"
echo "=================================================="

exec > >(tee ./repo-publication-consistency.log) 2>&1
