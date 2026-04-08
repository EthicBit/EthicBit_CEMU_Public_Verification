# ETHICBIT / CEMU v3.7.0+
## TRIPLE ANCHOR — ESPECIFICACIÓN TÉCNICA

**Estado:** `TECHNICAL_SPEC_LAYER_READY`  
**Estatus estructural:** `NOT_APPLICABLE`  
**Naturaleza:** especificación técnica subordinada del mecanismo de anclaje material  
**Finalidad:** describir el mecanismo técnico de anclaje múltiple y sus condiciones de verificabilidad material

## I. Objeto

La presente especificación técnica tiene por objeto describir el mecanismo de Triple Anchor del ecosistema EthicBit / CEMU v3.7.0+ como capa de anclaje material reforzado para artefactos sometidos a freeze, receipt, verification pack o verificación externa aplicable.

Su función consiste en fijar la arquitectura técnica mínima por la cual un mismo objeto puede quedar vinculado a tres planos de verificabilidad externa diferenciada:
- un plano L2 de anclaje transaccional y event-driven;
- un plano de persistencia permanente de contenido;
- y un plano de cómputo o verificación reproducible persistente.

## II. Regla rectora

El Triple Anchor no sustituye el bundle soberano ni redefine la autoridad constitutiva del núcleo.  
Su función es reforzar verificabilidad material, permanencia, contraste externo y reproducibilidad.

En consecuencia:
- el núcleo soberano sigue fijando identidad;
- el bundle soberano sigue fijando el objeto congelado;
- el Anchor Receipt sigue documentando el vínculo;
- y el Triple Anchor añade verificabilidad material por capas.

## III. Componentes del Triple Anchor

El Triple Anchor queda compuesto por tres planos diferenciados:

### A. Anchor L2
Plano de anclaje transaccional sobre red blockchain compatible.

### B. Anchor de persistencia permanente
Plano de persistencia durable del artefacto o de su representación verificable.

### C. Anchor de compute o verificación persistente
Plano de revalidación, replay o contraste verificable prolongado.

## IV. Plano L2

### 1. Función
Aportar:
- timestamp verificable;
- registro transaccional;
- receipt;
- bloque;
- y evento ABI decodificable.

### 2. Elementos mínimos verificables
- transaction hash
- receipt
- block number o bloque equivalente
- contrato aplicable
- evento emitido
- campo de vínculo, como `bundleRootHash` u homólogo

### 3. Tecnología de mercado compatible
- Ethereum L2
- rollups equivalentes
- redes EVM compatibles
- infraestructuras equivalentes con receipt y evento verificable

### 4. Criterio mínimo de suficiencia
El anchor L2 no se reputa materialmente verificado si no existe:
- transacción alcanzable;
- receipt verificable;
- evento ABI decodificado;
- y concordancia del campo material esperado.

## V. Plano de persistencia permanente

### 1. Función
Aportar:
- permanencia durable;
- recuperación posterior;
- verificabilidad de contenido;
- y contraste entre hash esperado y contenido observado.

### 2. Elementos mínimos verificables
- identificador de objeto
- disponibilidad del contenido
- hash real del contenido recuperado
- concordancia con el hash esperado
- persistencia no efímera

### 3. Tecnología de mercado compatible
- Arweave
- almacenamiento inmutable equivalente
- capas equivalentes de persistencia verificable

### 4. Criterio mínimo de suficiencia
La persistencia no se reputa materialmente verificada si:
- el contenido no existe;
- no puede recuperarse;
- el hash real no coincide;
- o la capa de persistencia no ofrece garantías suficientes de durabilidad.

## VI. Plano de compute o verificación persistente

### 1. Función
Aportar:
- replay;
- verificación reproducible;
- revalidación prolongada;
- y persistencia ejecutable del proceso de contraste.

### 2. Elementos mínimos verificables
- endpoint o process identificable
- alcanzabilidad suficiente
- vínculo con el objeto o hash material esperado
- concordancia del `bundleRootHash` u homólogo
- capacidad de revalidación o consulta persistente

### 3. Tecnología de mercado compatible
- AO
- capas equivalentes de cómputo persistente
- runners verificables persistentes
- workers auditables equivalentes

### 4. Criterio mínimo de suficiencia
El plano compute no se reputa materialmente verificado si:
- no existe endpoint o process verificable;
- no hay alcanzabilidad suficiente;
- no hay concordancia del identificador material esperado;
- o la capa no permite contraste reproducible bastante.

## VII. Convergencia del Triple Anchor

La convergencia material del Triple Anchor requiere evaluar conjuntamente:

1. validez del anclaje L2  
2. validez de la persistencia permanente  
3. validez del plano compute o verificación persistente

Estados mínimos posibles:
- `EXTERNAL_TRIPLE_ANCHOR_PARTIAL_OR_PENDING`
- `EXTERNAL_TRIPLE_ANCHOR_MATERIAL_VERIFIED`

## VIII. Regla de no equivalencia

El Triple Anchor no equivale por sí solo a:
- clausura formal;
- freeze principal;
- bundle soberano;
- ni verification pack completo.

Su función es reforzar verificabilidad material externa, no sustituir la secuencia constitucional del sistema.

## IX. Relación con Anchor Receipt

El Triple Anchor se relaciona con el Anchor Receipt del siguiente modo:
- el Anchor Receipt documenta el vínculo externo;
- el Triple Anchor aporta la verificabilidad material de sus capas.

En consecuencia:
- receipt sin verificabilidad material bastante no equivale a convergencia plena;
- Triple Anchor parcial no equivale a cierre fuerte;
- y receipt + anchor convergente refuerzan verificabilidad, pero siguen subordinados al flujo aplicable.

## X. Causales típicas de fallo

El Triple Anchor deberá reputarse parcial, pendiente o insuficiente cuando ocurra cualquiera de estas situaciones:
- ausencia de transacción verificable en L2
- receipt ausente o inconsistente
- evento ABI no decodificable
- mismatch del campo material esperado
- objeto persistente inexistente
- hash real no coincidente
- process o endpoint no alcanzable
- falta de concordancia del `bundleRootHash`
- o cualquier inconsistencia que impida sostener verificabilidad material bastante

## XI. Fórmula breve final

El Triple Anchor no añade retórica.  
Añade contraste externo por capas:
- transacción verificable,
- persistencia verificable,
- y compute verificable.

Solo cuando esas capas convergen puede sostenerse verificabilidad material reforzada.

## XII. Veredicto final

La presente especificación técnica fija el mecanismo de Triple Anchor como capa subordinada de anclaje material reforzado dentro del ecosistema EthicBit / CEMU v3.7.0+, apta para integrarse al tramo endurecido del Swarm MVP y al régimen general de verificación externa.
