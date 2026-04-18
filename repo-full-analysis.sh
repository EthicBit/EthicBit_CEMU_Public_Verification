#!/bin/bash
echo "=================================================="
echo "🔍 ETHICBIT CEMU - ANÁLISIS COMPLETO DEL REPOSITORIO"
echo "📍 $(pwd)"
echo "🕒 $(date)"
echo "=================================================="
echo

echo "=== 1. Estructura del proyecto ==="
ls -la

echo
echo "=== 2. Git status ==="
if [ -d .git ]; then
    git status --short
    echo
    git branch --show-current
    echo
    git log --oneline -8
else
    echo "❌ No es un repositorio Git"
fi

echo
echo "=== 3. Archivos críticos (Master State) ==="
ls -l docs/technical/EthicBit_CEMU_v3_7_0_plus_Master_State_Document_v1_3.md 2>/dev/null || echo "⚠️ Master MD no encontrado"
ls -l artifacts/history/ 2>/dev/null || echo "⚠️ Carpeta artifacts no encontrada"
ls -l results/ 2>/dev/null || echo "⚠️ Carpeta results no encontrada"

echo
echo "=== 4. Verificación rápida de estado actual ==="
echo "PACK_STATE=ACTIVE_CANONICAL → $(grep -o 'PACK_STATE=ACTIVE_CANONICAL' docs/technical/EthicBit_CEMU_v3_7_0_plus_Master_State_Document_v1_3.md 2>/dev/null || echo NO)"
echo "ANCHOR_HARDENING_ENABLED=PASS → $(grep -o 'ANCHOR_HARDENING_ENABLED=PASS' ./artifacts/history/swarm/anchor_hardening_declaration.txt 2>/dev/null || echo NO)"
echo "READY_FOR_CONTROLLED_PRODUCTION_CANDIDATE → $(grep -o 'READY_FOR_CONTROLLED_PRODUCTION_CANDIDATE' docs/technical/EthicBit_CEMU_v3_7_0_plus_Master_State_Document_v1_3.md 2>/dev/null || echo NO)"

echo
echo "=== 5. Hashes de archivos clave ==="
hash_file() {
    if [ -f "$1" ]; then
        shasum -a 256 "$1" | awk '{print $1}'
    else
        echo "NO_ENCONTRADO"
    fi
}

MASTER_HASH=$(hash_file "docs/technical/EthicBit_CEMU_v3_7_0_plus_Master_State_Document_v1_3.md")
echo "Master State Document hash → $MASTER_HASH"

echo
echo "=================================================="
echo "✅ ANÁLISIS COMPLETO TERMINADO"
echo "Log guardado → ./repo-full-analysis.log"
echo "=================================================="

# Guardar toda la salida
exec > >(tee ./repo-full-analysis.log) 2>&1
