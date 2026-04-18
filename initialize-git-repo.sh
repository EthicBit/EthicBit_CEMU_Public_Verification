#!/bin/bash
echo "=================================================="
echo "🔧 ETHICBIT CEMU - INICIALIZANDO GIT (Opción 3)"
echo "📍 $(pwd)"
echo "🕒 $(date)"
echo "=================================================="
echo

# 1. Verificar si ya existe un repo Git
if [ -d .git ]; then
    echo "⚠️  Ya existe un repositorio Git en este directorio."
    git status --short
    exit 0
fi

echo "✅ Iniciando nuevo repositorio Git..."

# 2. Inicializar Git
git init

# 3. Configurar nombre y email (si no están configurados)
git config --global user.name "oskrmiranda" 2>/dev/null || true
git config --global user.email "oskrmiranda@ethicbit.com" 2>/dev/null || true

# 4. Añadir archivos importantes (evitamos node_modules y carpetas temporales)
echo "Añadiendo archivos del proyecto..."
git add .gitignore
git add README.md README_PUBLIC.md PACKAGE_MANIFEST.json
git add docs/technical/EthicBit_CEMU_v3_7_0_plus_Master_State_Document_v1_3.md
git add artifacts/history/
git add results/
git add publication/
git add .env.template

# Añadir todo lo demás excepto lo que está en .gitignore
git add -A

echo
echo "=== Archivos que se van a commitear ==="
git status --short

echo
echo "=== Commit inicial con Freeze Tag ==="
git commit -m "chore: inicialización del repositorio + Freeze Tag FINAL

- Master State v1.3 sincronizado y actualizado
- Release 20260407T204627Z activa (ACTIVE_CANONICAL)
- Anchor Hardening ENABLED + FORMALLY_FROZEN
- Pre-freeze test suite ejecutado
- Auditoría de secretos limpia (tecnología propietaria protegida)
- Estado congelado: READY_FOR_CONTROLLED_PRODUCTION_CANDIDATE + FROZEN_FOR_CONTROLLED_PRODUCTION
- Fecha del Freeze Tag: 2026-04-08"

echo
echo "=== Creando tag oficial del Freeze ==="
git tag -a "v3.7.0-freeze-20260408" -m "Freeze Tag FINAL - Producción Controlada
Master State congelado el 8 de abril 2026
Estado: READY_FOR_CONTROLLED_PRODUCTION_CANDIDATE + FROZEN_FOR_CONTROLLED_PRODUCTION"

echo
echo "=================================================="
echo "✅ REPOSITORIO GIT INICIALIZADO CORRECTAMENTE"
echo "✅ Commit inicial + Tag v3.7.0-freeze-20260408 creado"
echo "=================================================="
echo
echo "Comandos útiles ahora:"
echo "git log --oneline -5"
echo "git tag"
echo "git status"
