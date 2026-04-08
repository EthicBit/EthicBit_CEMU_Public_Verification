#!/bin/bash
echo "=================================================="
echo "🔍 ETHICBIT CEMU - ANÁLISIS PROFUNDO DEL REPOSITORIO"
echo "📍 $(pwd)"
echo "🕒 $(date)"
echo "=================================================="
echo

echo "=== 1. Árbol completo de carpetas clave ==="
echo "docs/technical/"
find docs/technical -type f | sort
echo
echo "artifacts/history/"
find artifacts/history -type f | sort
echo
echo "results/"
find results -type f | sort
echo
echo "publication/"
find publication -type f 2>/dev/null | sort || echo "⚠️ Carpeta publication vacía o no existe"

echo
echo "=== 2. Contenido clave de los resultados (JSON) ==="
echo "=== index.json ==="
jq '.' results/index.json 2>/dev/null || cat results/index.json

echo
echo "=== GATE_REPORT.json ==="
jq '.' results/GATE_REPORT.json 2>/dev/null || cat results/GATE_REPORT.json

echo
echo "=== 3. Manifiestos de hashes anteriores ==="
ls -l artifacts/history/verification/ 2>/dev/null || echo "⚠️ No hay carpeta de verification aún"
echo
find artifacts/history/verification -name "*.json" 2>/dev/null | head -5

echo
echo "=== 4. Archivos más recientes del proyecto ==="
find . -type f -mtime -7 -ls | sort -k 11 | tail -15

echo
echo "=== 5. Hash completo del Master State Document (verificación) ==="
shasum -a 256 docs/technical/EthicBit_CEMU_v3_7_0_plus_Master_State_Document_v1_3.md

echo
echo "=================================================="
echo "✅ ANÁLISIS PROFUNDO TERMINADO"
echo "Log guardado → ./repo-deep-analysis.log"
echo "=================================================="

exec > >(tee ./repo-deep-analysis.log) 2>&1
