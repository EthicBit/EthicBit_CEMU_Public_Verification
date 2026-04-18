#!/bin/bash
echo "=================================================="
echo "🔍 ETHICBIT CEMU - VERIFICACIÓN MASTER STATE vs PUBLICACIÓN"
echo "📍 $(pwd)"
echo "🕒 $(date)"
echo "=================================================="
echo

MASTER_MD="docs/technical/EthicBit_CEMU_v3_7_0_plus_Master_State_Document_v1_3.md"
RELEASE_ID="release-20260407T204627Z"

echo "=== 1. Fecha del Master State Document ==="
ls -l "$MASTER_MD"

echo
echo "=== 2. Secciones relevantes del Master State (búsqueda de estado actual) ==="
echo "=== PACK_STATE, ANCHOR_HARDENING y READY ==="
grep -n -E 'PACK_STATE|ANCHOR_HARDENING_ENABLED|READY_FOR_CONTROLLED_PRODUCTION_CANDIDATE' "$MASTER_MD"

echo
echo "=== 3. Búsqueda específica de publicación y release ==="
echo "Menciones a 'publication', 'release', '20260407', 'canonical' o 'closure':"
grep -n -E 'publication|release|20260407|canonical|closure|frozen' "$MASTER_MD" || echo "No se encontraron menciones"

echo
echo "=== 4. Estado declarado en el Master State (últimas líneas relevantes) ==="
tail -n 80 "$MASTER_MD" | grep -E 'verifiedState|declaredState|packState|publicationState|operationalReadiness' -A 30 || echo "No se encontró sección de verifiedState"

echo
echo "=== 5. Comparación con publication_state.json ==="
echo "Estado actual en publication_state.json:"
cat publication/publication_state.json 2>/dev/null | jq '.' || cat publication/publication_state.json

echo
echo "=== 6. Resumen de consistencia ==="
echo "Master State menciona release actual? → $(grep -q "$RELEASE_ID" "$MASTER_MD" && echo "SÍ" || echo "NO")"
echo "Certificado de cierre en Master State? → $(grep -q "FORMALLY_FROZEN" "$MASTER_MD" && echo "SÍ" || echo "NO")"

echo
echo "=================================================="
echo "✅ VERIFICACIÓN MASTER STATE vs PUBLICACIÓN TERMINADA"
echo "Log guardado → ./master-state-vs-publication.log"
echo "=================================================="

exec > >(tee ./master-state-vs-publication.log) 2>&1
