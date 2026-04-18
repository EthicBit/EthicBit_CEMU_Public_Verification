#!/usr/bin/env bash
set -euo pipefail

cat > "docs/technical/EthicBit_CEMU_v3_7_0_plus_Swarm_Verification_Pack_Implementation.md" <<'EOF'
# ETHICBIT / CEMU v3.7.0+
## SWARM VERIFICATION PACK — IMPLEMENTACIÓN TÉCNICA

**Estado:** `TECHNICAL_SPEC_LAYER_READY`  
**Estatus estructural:** `NOT_APPLICABLE`  
**Naturaleza:** especificación técnica subordinada del artefacto central de verificación interna  
**Finalidad:** detallar la implementación técnica del verification pack dentro del tramo swarm endurecido

## I. Objeto

La presente especificación técnica tiene por objeto describir la implementación del verification pack dentro del tramo endurecido del Swarm MVP del ecosistema EthicBit / CEMU v3.7.0+.

Su función consiste en fijar:
- la naturaleza del verification pack;
- su posición dentro del flujo de verificación;
- su relación con bundle, agent receipts, collective pack y anchor receipt;
- su disciplinamiento criptográfico;
- y su relación con certificate-linkage, external verification y closure.

## II. Regla rectora

El verification pack no sustituye:
- al bundle soberano;
- al Anchor Receipt;
- al certificate-linkage;
- ni al Formal Closure Certificate.

Su función es intermedia, verificadora y reproducible.

En consecuencia:
- organiza evidencia interna de verificación;
- consolida consistencia estructural del stack;
- puede ser firmado;
- puede servir como base de linkage;
- pero no equivale por sí solo a clausura formal.

## III. Posición del verification pack en el flujo

El verification pack se ubica entre:
1. artefactos base del swarm ya emitidos;
2. verificación interna del stack;
3. firma del verification pack;
4. emisión del certificate-linkage;
5. verificación externa del triple anchor;
6. verificación criptográfica final;
7. y eventual declarabilidad de cierre fuerte.

## IV. Artefactos mínimos que alimentan el verification pack

El verification pack se construye, como mínimo, a partir de estos artefactos:

- `security_incident_bundle_v1_0.json`
- `agent-receipt.kiro.json`
- `agent-receipt.luna.json`
- `agent-receipt.echo.json`
- `collective-pack.swarm_mvp_v1.canonical.json`
- `anchor-receipt.swarm_mvp_v1.canonical.json`

## V. Finalidades técnicas del verification pack

El verification pack cumple, como mínimo, las siguientes finalidades:

### A. Consolidación estructural
Concentrar en un solo artefacto el resultado verificable de consistencia del stack.

### B. Trazabilidad reproducible
Permitir que terceros o verificadores internos reproduzcan la verificación del tramo aplicable.

### C. Base de linkage
Servir como base subordinante del `certificate-linkage`.

### D. Base de firma
Permitir una firma persistente del coordinator sobre un artefacto verificativo intermedio.

### E. Fail-closed
Bloquear elevaciones indebidas cuando el stack no alcanza suficiencia material.

## VI. Estructura funcional mínima

El verification pack deberá contener, como mínimo cuando proceda, bloques funcionales equivalentes a los siguientes:

### 1. Identificación del artefacto
- nombre del artefacto
- versión aplicable
- tipo documental o técnico
- timestamp de emisión
- estado observado

### 2. Referencias a artefactos fuente
- incident bundle
- agent receipts
- collective pack
- anchor receipt

### 3. Resultados de verificación interna
- consistencia estructural
- integridad mínima
- concordancias verificadas
- mismatches detectados, si existieran
- estado resultante

### 4. Hashing y canonicalización
- forma canónica usada
- hash del artefacto emitido
- reglas de serialización aplicables

### 5. Firma, cuando proceda
- campo `signature`
- algoritmo
- `publicKey`
- metadata suficiente de verificación

## VII. Estados mínimos esperables

El verification pack deberá poder expresar, como mínimo, estados como:

- `SWARM_VERIFICATION_PACK_CANONICAL_HONEST_DEMO_READY`
- `SWARM_VERIFICATION_PACK_MATERIAL_FINAL_VERIFIABLE`
- `SWARM_VERIFICATION_PACK_SIGNED_CANONICAL_HONEST_DEMO_READY`
- `SWARM_VERIFICATION_PACK_SIGNED_MATERIAL_FINAL_VERIFIABLE`

## VIII. Variante no firmada y variante firmada

### A. Variante no firmada
Corresponde al resultado de `verify_swarm_stack_async.py`.

Su función es verificar y consolidar internamente el stack antes de aplicar firma persistente.

### B. Variante firmada
Corresponde al resultado de `verify_swarm_stack_async_signed.py`.

Su función es:
- fijar la verificación observada;
- someter el artefacto a firma persistente del coordinator;
- y convertir el verification pack en base verificativa criptográficamente reforzada.

## IX. Relación con certificate-linkage

El `certificate-linkage` no debe nacer autónomamente.

Debe depender estructuralmente del estado real del verification pack.

En consecuencia:
- verification pack suficiente → puede habilitar linkage subordinado;
- verification pack insuficiente → bloquea linkage declarable;
- verification pack firmado → refuerza linkage firmado;
- verification pack no materialmente verificable → impide elevación fuerte.

## X. Controles mínimos de implementación

Toda implementación técnica del verification pack deberá verificar, como mínimo:

- existencia de artefactos fuente requeridos
- consistencia mínima entre hashes esperados y observados
- consistencia de nombres y rutas esperadas
- canonicalización coherente
- generación reproducible del artefacto
- fail-closed si faltan insumos críticos
- firma solo cuando la clave persistente esté disponible
- bloqueo de elevación si el estado no alcanza umbral suficiente

## XI. Causales típicas de fallo

La implementación deberá reputarse insuficiente cuando ocurra cualquiera de estas situaciones:
- falta de incident bundle
- falta de receipts requeridos
- falta de collective pack
- falta de anchor receipt
- mismatches estructurales no resueltos
- canonicalización inconsistente
- firma ausente cuando era obligatoria
- publicKey inconsistente
- emisión de linkage sin soporte suficiente del verification pack
- o cualquier inconsistencia que degrade reproducibilidad verificable

## XII. Relación con verificabilidad externa

El verification pack prepara la verificabilidad externa, pero no la sustituye.

Su función correcta es:
- dejar el stack internamente consistente y verificable;
- servir de base a la verificación externa;
- y permitir transición disciplinada al tramo de anchors y firmas finales.

No equivale por sí solo a:
- verificación material del triple anchor;
- ni a `SWARM_FORMAL_CLOSURE_DECLARABLE`.

## XIII. Fórmula breve final

El verification pack no cierra el sistema.  
Lo disciplina, lo verifica y lo deja apto para avanzar al siguiente umbral de verificabilidad.

## XIV. Veredicto final

La presente especificación técnica fija la implementación del verification pack como artefacto central de verificación interna reproducible dentro del tramo endurecido del Swarm MVP del ecosistema EthicBit / CEMU v3.7.0+.
EOF

echo "VERIFICATION_PACK_IMPL_LOADED"