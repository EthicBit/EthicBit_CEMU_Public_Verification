#!/usr/bin/env bash
set -euo pipefail

cat > "docs/guides/EthicBit_CEMU_v3_7_0_plus_Swarm_MVP_Implementation_Guide.md" <<'EOF'
# ETHICBIT / CEMU v3.7.0+
## GUÍA OFICIAL DE IMPLEMENTACIÓN SWARM MVP

**Estado:** `GUIDE_LAYER_INTEGRATED`  
**Estatus estructural:** `NOT_APPLICABLE`  
**Naturaleza:** guía práctica subordinada de implementación operativa  
**Finalidad:** describir la implementación práctica del Swarm MVP en términos ejecutables y ordenados

## I. Objeto

La presente guía tiene por objeto traducir el baseline, la ruta previa, el runbook endurecido y las especificaciones técnicas del Swarm MVP a una secuencia práctica de implementación operativa dentro de un entorno local disciplinado.

Su función consiste en indicar:
- qué debe existir antes de ejecutar;
- en qué orden debe organizarse el repositorio;
- qué artefactos mínimos deben estar presentes;
- qué scripts se ejecutan;
- y cómo distinguir preparación, ejecución local, materialización externa y declarabilidad final.

## II. Regla rectora

La implementación correcta del Swarm MVP no empieza por el gasto externo ni por la ejecución ciega del stack.

Empieza por:
1. fijación documental;
2. freeze editorial;
3. estructura real de repo;
4. entorno local disciplinado;
5. ejecución local completa;
6. materialización externa real, si procede;
7. evaluación final de convergencia.

## III. Estructura mínima de repo

La implementación práctica parte de una estructura mínima como la siguiente:

```text
EthicBit_CEMU/
├─ docs/
├─ scripts/
│  └─ swarm/
├─ artifacts/
│  └─ swarm/
├─ keys/
├─ contracts/
└─ .env