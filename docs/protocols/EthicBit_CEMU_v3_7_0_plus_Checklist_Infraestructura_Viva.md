# ETHICBIT / CEMU v3.7.0+

## CHECKLIST OPERATIVA — TRANSICIÓN A INFRAESTRUCTURA VIVA

**Estado:** `LIVE_INFRASTRUCTURE_CHECKLIST_READY`  
**Estatus estructural:** `PRE_ACTIVATION_TRANSITION_CONTROL_ENABLED`  
**Naturaleza:** checklist subordinada de transición operativa a entorno funcional real  
**Finalidad:** identificar, en orden estricto, los requisitos faltantes para pasar de materialización estructural a integración en infraestructura viva

---

## I. Regla rectora

La infraestructura viva no comienza cuando el repo “se ve completo”, sino cuando los componentes críticos dejan de ser placeholder y pasan a:

- estar conectados a red real o entorno real controlado;
- ejecutar lógica real suficiente;
- producir artifacts reales verificables;
- y sostener evidencia material del flujo.

En consecuencia:

- estructura no equivale a activación;
- placeholder no equivale a operación;
- ABI cargado no equivale a anchor verificado;
- documentación reconciliada no equivale a cierre real;
- compilación satisfactoria no equivale a despliegue vivo;
- artifact local canónico no equivale por sí solo a artifact on-chain verificado.

---

## II. Checklist maestra de transición

### 1. `.env` real y no plantillado

**Objetivo:** sustituir valores placeholder por parámetros reales.

**Debe quedar resuelto:**
- `ETH_RPC_URL` real
- gateways reales si aplican
- cualquier endpoint productivo o de staging
- parámetros finales de red y entorno
- dirección pública real de cuenta operativa
- private key hex real de despliegue cuando aplique

**Criterio de cumplimiento:**  
el `.env` ya no contiene placeholders del tipo `REEMPLAZA_...`, `TU_API_KEY`, `TU_RPC`, etc., en los campos críticos de despliegue y verificación.

**Estado actual estimado:** parcial estructural  
**Lectura correcta:** `.env` ya está ordenado y alineado en forma, pero aún no contiene todos los parámetros reales necesarios para despliegue y anchor vivo.

---

### 2. Contrato real identificado

**Objetivo:** fijar el contrato real de operación.

**Debe quedar resuelto:**
- `CONTRACT_ADDRESS` real
- `chainId` real
- red real objetivo
- confirmación de si el contrato ya está desplegado o no

**Criterio de cumplimiento:**  
existe una dirección de contrato viva, verificable y asociada al entorno elegido.

**Estado actual estimado:** pendiente

---

### 3. ABI real integrado y validado

**Objetivo:** asegurar compatibilidad con el contrato real.

**Debe quedar resuelto:**
- `contracts/ClosureAnchor.abi.json` con ABI real
- confirmación de:
  - evento `ClosureAnchored`
  - campo `rootHash`
  - función `isAnchored`

**Criterio de cumplimiento:**  
el ABI real permite decodificación y lectura real del contrato.

**Estado actual estimado:** cumplido

---

### 4. Alineación total de variables con el ABI real

**Objetivo:** evitar desajustes entre contrato y configuración.

**Debe quedar resuelto:**
- `L2_ANCHOR_EVENT_NAME=ClosureAnchored`
- `L2_ANCHOR_EVENT_FIELD=rootHash`

**Criterio de cumplimiento:**  
`.env` y scripts usan nombres reales del contrato.

**Estado actual estimado:** cumplido

---

### 5. Política de llaves definida

**Objetivo:** decidir si el entorno operará con llaves de prueba o llaves definitivas.

**Debe quedar resuelto:**
- mantener llaves de test, o
- sustituir por llaves reales,
- y documentar el estatus del entorno

**Criterio de cumplimiento:**  
las llaves utilizadas son coherentes con el tipo de entorno (test, staging, producción) y con el método real de despliegue.

**Estado actual estimado:** parcial

---

### 6. Scripts del flujo implementados realmente

**Objetivo:** sustituir placeholders por lógica real.

**Debe quedar resuelto en:**
- `scripts/deploy_closure_anchor.js`
- `scripts/anchor_closure.js`
- `verify_closure_anchor_event.js`
- `scripts/swarm/verify_swarm_stack_async.py`
- `scripts/swarm/verify_swarm_stack_async_signed.py`
- `scripts/swarm/emit_certificate_linkage_async_signed.py`
- `scripts/swarm/verify_external_anchors_async.py`
- `scripts/swarm/verify_coordinator_signatures.py`

**Criterio de cumplimiento:**  
los scripts ejecutan funciones reales del flujo y no solo imprimen placeholders.

**Estado actual estimado:** parcial

**Lectura correcta:**  
el bloque mínimo de deploy, anchor y verificación on-chain ya está materializado; el bloque swarm asíncrono todavía no se considera funcionalmente cerrado de punta a punta.

---

### 7. Artifacts base con contenido real

**Objetivo:** sustituir JSON placeholder por material real del flujo.

**Debe quedar resuelto en:**
- `security_incident_bundle_v1_0.json`
- `agent-receipt.kiro.json`
- `agent-receipt.luna.json`
- `agent-receipt.echo.json`
- `collective-pack.swarm_mvp_v1.canonical.json`
- `anchor-receipt.swarm_mvp_v1.canonical.json`

**Criterio de cumplimiento:**  
los artifacts contienen datos materiales reales y no solo estructura vacía o placeholder.

**Estado actual estimado:** parcial avanzado

**Lectura correcta:**  
ya existen artifacts base locales materializados para bundle, collective pack y anchor receipt local, pero todavía faltan:
- endurecimiento con datos reales on-chain;
- algunos hashes de evidencia;
- y receipts/agentes complementarios si son parte del flujo efectivo de cierre.

---

### 8. Primera ejecución local disciplinada

**Objetivo:** demostrar que el stack corre localmente con consistencia.

**Secuencia mínima:**
1. verificación interna  
2. firma  
3. certificate-linkage  
4. verificación externa  
5. verificación de firmas

**Criterio de cumplimiento:**  
la secuencia corre de punta a punta sin contradicción estructural grave y genera artifacts de salida.

**Estado actual estimado:** parcial

**Lectura correcta:**  
el repositorio ya permite avance real en compilación, deploy, anchor y verificación básica, pero todavía no consta una ejecución disciplinada integral del flujo completo.

---

### 9. Verificación on-chain real

**Objetivo:** probar la capa viva del contrato con datos reales.

**Debe quedar resuelto:**
- script `verify_closure_anchor_event.js` ejecutado con:
  - `RPC_URL` real
  - `CONTRACT_ADDRESS` real
  - `ROOT_HASH` real
  - opcionalmente `TX_HASH`
  - `EXPECTED_CHAIN_ID` real

**Criterio de cumplimiento:**  
se obtiene evidencia real de verificación on-chain.

**Estado actual estimado:** pendiente

---

### 10. Verificación de convergencia

**Objetivo:** evaluar si el sistema ya salió de preparación y entró en estado funcional verificable.

**Debe quedar resuelto:**
- qué está completo
- qué está parcial
- qué sigue bloqueado
- qué ya puede elevarse

**Criterio de cumplimiento:**  
existe una evaluación fail-closed, clara y documentada del estado real del flujo.

**Estado actual estimado:** pendiente

---

### 11. Acta de activación operativa viva

**Objetivo:** dejar constancia formal del paso a infraestructura viva.

**Debe incluir, como mínimo:**
- red activa
- `chainId`
- `contract address`
- ABI real
- llaves/rol de firma
- entorno (`test`, `staging`, `prod`)
- fecha de activación
- criterio de operación habilitada

**Criterio de cumplimiento:**  
existe documento formal que marca la entrada en operación viva.

**Estado actual estimado:** pendiente

---

## III. Lectura de estado actual

### Ya cumplido
- estructura documental completa
- ABI real integrado
- `.env` alineado con el ABI real en su capa estructural
- documento técnico on-chain hardening integrado
- contrato `ClosureAnchor.sol` presente y compilando
- script de deploy presente
- script de anchor presente
- script de verificación on-chain presente
- scripts y artifacts con base estructural presente
- artifacts base locales ya materializados en versión canónica local

### Parcial
- llaves presentes, pero aún bajo lógica de prueba o no plenamente configuradas para despliegue vivo
- entorno local alineado, pero todavía no activado con parámetros reales
- `.env` limpio, pero con placeholders en variables críticas
- bloque swarm parcialmente implementado, pero no íntegramente ejecutado en flujo real
- artifacts base reales locales, pero todavía no completamente endurecidos con todos los hashes y receipts finales

### Pendiente crítico
- parámetros reales del entorno
- `ETH_RPC_URL` real
- `ETHICBIT_ACCOUNT_ADDRESS` real
- `DEPLOYER_PRIVATE_KEY` real
- contrato real identificado/desplegado
- `ETHICBIT_CONTRACT_ADDRESS` real
- `TX_HASH` real
- scripts funcionales reales de punta a punta en flujo vivo
- artifacts complementarios reales
- primera ejecución local real disciplinada
- verificación on-chain real
- acta de activación viva

---

## IV. Cuello de botella principal

El cuello de botella actual no es documental.

El cuello de botella actual es funcional y se concentra en este trío:

1. parámetros reales del entorno  
2. contrato real y dirección real  
3. ejecución real con artifacts reales y verificación on-chain suficiente

---

## V. Orden exacto recomendado

### Fase inmediata
1. fijar `.env` real  
2. fijar `CONTRACT_ADDRESS` y `chainId` reales  
3. confirmar despliegue o desplegar el contrato si falta  

### Fase técnica funcional
4. terminar de implementar scripts reales del flujo aplicable  
5. reemplazar artifacts placeholder restantes por artifacts reales  
6. endurecer artifacts base con datos reales finales  

### Fase de prueba
7. primera ejecución local disciplinada  
8. verificación on-chain real  

### Fase de activación
9. evaluación de convergencia  
10. acta de activación operativa viva  

---

## VI. Regla de paso a infraestructura viva

No deberá sostenerse que EthicBit / CEMU ha entrado en infraestructura viva mientras no concurran, como mínimo:

- ABI real
- variables reales de entorno
- contrato real identificado
- scripts reales suficientes
- artifacts reales suficientes
- primera ejecución local real
- y verificación on-chain real suficiente

---

## VII. Fórmula breve final

La infraestructura viva empieza cuando:

- el contrato es real,
- la red es real,
- el entorno es real,
- los scripts son reales,
- los artifacts son reales,
- y la verificación deja de ser hipotética.

---

## VIII. Veredicto final

El ecosistema EthicBit / CEMU v3.7.0+ se encuentra actualmente en un estado de **preintegración estructural avanzada**, con base documental y técnica suficientemente ordenada, y con base canónica local ya materializada para varias piezas clave, pero todavía sin cierre funcional real de infraestructura viva.

La transición correcta exige ahora activación progresiva de:

- parámetros reales,
- contrato real,
- scripts realmente ejecutados,
- artifacts materialmente completos,
- ejecución local real,
- y verificación on-chain real.

**Estatus final de la checklist:**
- `LIVE_INFRASTRUCTURE_CHECKLIST_READY`
- `PRE_ACTIVATION_TRANSITION_CONTROL_ENABLED`
- `FUNCTIONAL_REAL_ALIGNMENT_PENDING`

---

## IX. Ruta de integración al repo

**Nombre exacto recomendado:**

```text
EthicBit_CEMU_v3_7_0_plus_Checklist_Infraestructura_Viva.md
docs/protocols/EthicBit_CEMU_v3_7_0_plus_Checklist_Infraestructura_Viva.md
# 3. Validar que quedó bien
Ejecuta:

```bash id="w3lz7i"
sed -n '1,40p' docs/protocols/EthicBit_CEMU_v3_7_0_plus_Checklist_Infraestructura_Viva.md
tail -n 20 docs/protocols/EthicBit_CEMU_v3_7_0_plus_Checklist_Infraestructura_Viva.md
wc -l docs/protocols/EthicBit_CEMU_v3_7_0_plus_Checklist_Infraestructura_Viva.md
