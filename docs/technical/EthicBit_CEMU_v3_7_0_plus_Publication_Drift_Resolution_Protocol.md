# ETHICBIT / CEMU v3.7.0+
## PROTOCOLO FORMAL DE RESOLUCIÓN DE DRIFT DE PUBLICACIÓN

**Régimen de Canonización de Artefactos y Restitución de Fuente Activa Única**

**Código de estado de activación:** `PUBLICATION_DRIFT_DETECTED`  
**Estado objetivo:** `CANONICAL_PUBLICATION_RESTORED`  
**Naturaleza:** protocolo correctivo formal, no destructivo, trazable y fail-closed  
**Ámbito:** manifests, certificates, ledgers, receipts, bundles, verification packs y toda capa documental o técnica que participe en la cadena activa de cierre

---

## I. Objeto del protocolo

El presente protocolo tiene por objeto resolver formalmente situaciones de drift de publicación, entendidas como la coexistencia de múltiples artefactos activos, parcialmente divergentes o materialmente inconsistentes respecto del mismo cierre, bundle, certificate, manifest, ledger o cadena de verificación.

Su finalidad consiste en restituir una única fuente activa de verdad, preservar la trazabilidad de los artefactos previos, impedir inflación semántica del cierre y reabrir la posibilidad de verificación material coherente bajo régimen fail-closed.

---

## II. Declaración del problema habilitante

Se considera activado el presente protocolo cuando, respecto del mismo objeto de cierre, concurra al menos uno de los siguientes supuestos:

1. coexistencia de dos o más manifests materialmente incompatibles;  
2. coexistencia de dos o más certificates que pretendan vigencia simultánea;  
3. discrepancia entre ledger y certificate activo;  
4. discrepancia entre manifest y certificate;  
5. discrepancia entre incident bundle referenciado y su hash canónico real;  
6. persistencia visible de artefactos previos como si aún fueran fuente activa;  
7. o cualquier situación en la que existan varias “verdades publicadas” respecto del mismo cierre.

En tal caso, el estado correcto del sistema no será readiness de freeze, sino:

`PUBLICATION_DRIFT_DETECTED`

---

## III. Principio rector del protocolo

El principio rector del presente protocolo es el siguiente:

> **No se corrige el drift anclando más fuerte la divergencia; se corrige restituyendo una sola cadena canónica activa.**

En consecuencia:

- no deberá emitirse un nuevo anchor sobre una cadena documental ambigua;  
- no deberá afirmarse readiness final mientras subsistan fuentes activas múltiples;  
- y no deberá usarse endurecimiento criptográfico para encubrir desalineación de publicación.

---

## IV. Regla de freeze de publicación

Una vez activado el presente protocolo, deberá emitirse inmediatamente un estado de:

`PUBLICATION_FREEZE_ACTIVE`

Bajo este estado quedará suspendida toda nueva emisión activa de:

1. manifests;  
2. certificates;  
3. ledger updates;  
4. verification packs;  
5. receipts derivados;  
6. y cualquier publicación que aumente la ambigüedad de la cadena vigente.

La suspensión no implica borrado ni destrucción de artefactos previos; implica exclusivamente inmovilización temporal de la capa de publicación hasta restitución canónica completa.

---

## V. Regla de identificación del artefacto raíz canónico

Bajo el estado `PUBLICATION_FREEZE_ACTIVE`, deberá identificarse un único artefacto raíz canónico, que servirá como base de reconstrucción del resto de la cadena.

Como regla general:

1. el artefacto raíz deberá ser el más estable, verificable y materialmente consistente;  
2. no deberá elegirse por visibilidad pública accidental, sino por integridad canónica real;  
3. si el incidente gira en torno a un incident bundle, el hash canónico real del incident bundle prevalecerá sobre referencias documentales previas incorrectas.

El resultado de esta fase será un estado de:

`CANONICAL_ROOT_SELECTED`

---

## VI. Regla de regeneración no parcheada del certificate

Identificado el artefacto raíz canónico, deberá emitirse un nuevo certificate canónico, y no un simple parche del certificate previo.

La regeneración deberá cumplir, como mínimo, con lo siguiente:

1. referenciar exactamente el hash canónico real del incident bundle u objeto raíz;  
2. incorporar versión nueva o equivalente marca de sucesión;  
3. registrar expresamente la sustitución del certificate anterior;  
4. dejar trazabilidad del certificate sustituido;  
5. impedir que el certificate previo continúe apareciendo como vigente.

El resultado de esta fase será un estado de:

`CANONICAL_CERTIFICATE_EMITTED`

---

## VII. Regla de regeneración del manifest canónico

Emitido el nuevo certificate canónico, deberá emitirse un único manifest canónico activo, derivado exclusivamente de la nueva cadena corregida.

El nuevo manifest deberá:

1. apuntar al certificate canónico vigente;  
2. apuntar al incident bundle raíz correcto;  
3. excluir cualquier referencia activa a certificates o manifests previos;  
4. incorporar marca de sustitución o sucesión cuando corresponda;  
5. y quedar constituido como única fuente activa de publicación documental del cierre.

El resultado de esta fase será un estado de:

`CANONICAL_MANIFEST_EMITTED`

---

## VIII. Regla de corrección del ledger

Una vez emitidos certificate y manifest canónicos, el ledger deberá ser corregido para reflejar exclusivamente la cadena nueva como fuente activa.

La corrección del ledger deberá:

1. alinear incident bundle, certificate y manifest;  
2. retirar vigencia activa a referencias anteriores incompatibles;  
3. preservar trazabilidad histórica de versiones previas;  
4. impedir que el ledger continúe exponiendo un artifact anterior como si fuese vigente.

El resultado de esta fase será un estado de:

`LEDGER_REALIGNED_TO_CANONICAL_CHAIN`

---

## IX. Regla de no destrucción y supersession trazable

Todo artifact previamente publicado y hoy desplazado por la cadena corregida no deberá ser destruido, sino reclasificado.

La clasificación correcta de todo artifact previo incompatible será:

`SUPERSEDED_BUT_TRACEABLE`

Esta regla produce los siguientes efectos:

1. conserva genealogía documental;  
2. impide pérdida de historia;  
3. evita apariencia de manipulación destructiva;  
4. y restituye una sola fuente activa sin negar la existencia de versiones previas.

---

## X. Regla de fuente activa única

Concluidas las fases anteriores, deberá quedar restituida una sola fuente activa de verdad para el cierre correspondiente.

La cadena activa única deberá estar compuesta, como mínimo, por:

1. artifact raíz canónico;  
2. certificate canónico vigente;  
3. manifest canónico vigente;  
4. ledger alineado;  
5. y verification pack coherente cuando corresponda.

A partir de este punto, la clasificación correcta será:

- cadena nueva: `ACTIVE_CANONICAL`  
- cadena previa: `SUPERSEDED_BUT_TRACEABLE`

No podrá coexistir más de una cadena con pretensión de vigencia activa sobre el mismo cierre.

---

## XI. Regla de endurecimiento posterior del anchor

Solo después de restituida la fuente activa única podrá procederse al endurecimiento del anchor.

En esta fase se habilita:

1. incorporación de `blockHash` al Anchor Receipt;  
2. validación conjunta de `blockNumber` y `blockHash`;  
3. propagación de `blockHash` al Formal Closure Certificate;  
4. y fortalecimiento anti-reorg de la verificación on-chain.

Se declara expresamente que esta fase:

- mejora robustez del anchor;  
- pero no sustituye la canonización previa;  
- y no debe ejecutarse como remedio primario del drift de publicación.

El resultado de esta fase será un estado de:

`ANCHOR_HARDENING_ENABLED`

---

## XII. Regla de revalidación integral

Restituida la cadena canónica y endurecido el anchor cuando proceda, deberá ejecutarse la revalidación integral del cierre, incluyendo como mínimo:

1. snapshot;  
2. bundle;  
3. receipt;  
4. certificate;  
5. manifest;  
6. verification pack;  
7. ledger;  
8. subgraph;  
9. dashboard;  
10. verificación criptográfica;  
11. y validación material aplicable.

Solo si toda la cadena converge a una sola verdad activa y verificable podrá emitirse el estado:

`CANONICAL_PUBLICATION_RESTORED`

Y solo con posterioridad, si además se cumplen las demás condiciones materiales del sistema, podrá reabrirse la evaluación de:

`READY_FOR_MATERIAL_FREEZE`

---

## XIII. Regla de prohibición de promoción prematura

Mientras subsista drift de publicación o mientras no haya sido restaurada la cadena canónica activa, queda prohibido:

1. declarar readiness final;  
2. afirmar cierre material total;  
3. afirmar freeze listo para promoción;  
4. o usar lenguaje de finalización plena.

Toda promoción emitida antes de cerrar el protocolo deberá reputarse doctrinalmente improcedente y materialmente inválida.

---

## XIV. Efectos del protocolo

La ejecución completa del presente protocolo produce los siguientes efectos:

1. congela la expansión del drift;  
2. identifica un artefacto raíz único;  
3. regenera certificate y manifest sin parche impropio;  
4. alinea el ledger con la cadena canónica;  
5. preserva trazabilidad histórica de artefactos previos;  
6. restituye una única fuente activa de verdad;  
7. habilita endurecimiento posterior del anchor;  
8. y reabre legítimamente la puerta a la revalidación final del cierre.

---

## XV. Fórmula ejecutiva del protocolo

> El drift de publicación no se resuelve con más publicación, sino con canonización, supersession trazable y restitución de una sola fuente activa de verdad.

---

## XVI. Fórmula breve de aplicación

Primero:

- freeze de publicación,  
- selección de raíz canónica,  
- regeneración de certificate,  
- regeneración de manifest,  
- corrección de ledger.

Después:

- supersession trazable,  
- integración de `blockHash`,  
- revalidación integral,  
- y solo entonces reconsideración del gate final.

---

## XVII. Veredicto final del protocolo

Cuando exista coexistencia de manifests, certificates o ledgers divergentes, el estado correcto no es readiness material, sino:

`PUBLICATION_DRIFT_DETECTED`

La solución correcta es:

> **canonizar primero; endurecer después.**

---

**PROTOCOLO FORMAL DE RESOLUCIÓN DE DRIFT DE PUBLICACIÓN**  
**EthicBit / CEMU v3.7.0+**  
Emitido como instrumento correctivo formal del régimen de cierre y publicación canónica.