# ETHICBIT / CEMU v3.7.0+
## VERIFICACIÓN ON-CHAIN REFORZADA CON `blockHash` — HARDENING ANTI-REORG

**Estado:** `TECHNICAL_HARDENING_LAYER_READY`  
**Estatus estructural:** `ANTI_REORG_HARDENING_VALID`  
**Naturaleza:** especificación técnica subordinada de endurecimiento de verificación on-chain  
**Finalidad:** reforzar la verificabilidad material del anchor on-chain mediante validación adicional de consistencia entre `blockNumber`, `blockHash`, receipt y evento emitido

## I. Objeto

La presente especificación tiene por objeto incorporar una capa reforzada de verificación on-chain dentro del ecosistema EthicBit / CEMU v3.7.0+ mediante la inclusión y validación de `blockHash` en el flujo de anchor, verificación y certificación final aplicable.

Su función consiste en endurecer la verificabilidad material del plano on-chain frente a:
- reorganizaciones de cadena;
- discrepancias históricas entre bloque observado y bloque persistido;
- inconsistencias entre receipt, evento y referencia de bloque;
- y cualquier intento de sostener verificabilidad material sobre una referencia de bloque no suficientemente estable.

## II. Regla rectora

La incorporación de `blockHash` no redefine la autoridad constitutiva del núcleo, ni sustituye el bundle soberano, ni convierte por sí sola el anclaje en clausura formal.

Su función correcta es reforzar la verificabilidad material del plano on-chain mediante una validación adicional de consistencia entre:
- transacción observada;
- número de bloque registrado;
- hash del bloque registrado;
- y evento emitido.

En consecuencia:
- la mejora endurece la verificación;
- mantiene la disciplina fail-closed;
- y vuelve detectable cualquier inconsistencia relevante derivada de reorgs o manipulación de referencias de bloque.

## III. Cambio funcional introducido

La presente mejora introduce los siguientes cambios mínimos y de alto impacto:

### A. Extensión del `Anchor Receipt`
El `Anchor Receipt` incorpora el campo:

- `blockHash`

como hash exacto del bloque confirmado en el que fue observada la transacción de anchor.

### B. Extensión de `anchor.py`
El flujo de anchor captura `blockHash` inmediatamente después de obtener el `transaction_receipt` confirmado y de recuperar el bloque correspondiente.

### C. Extensión de `status.py verify`
La verificación soberana del evento deja de depender solo de:
- `blockNumber`

y pasa a exigir además:
- `blockHash`

### D. Extensión del `FormalClosureCertificate`
El certificado final podrá incorporar también `blockHash`, reforzando trazabilidad histórica del anclaje observado.

## IV. Formato reforzado del `Anchor Receipt`

El `Anchor Receipt` reforzado deberá contener, como mínimo, la siguiente estructura:

```json
{
  "bundleId": "bundle-ezkl-20250322-001",
  "bundleRootHash": "0x1234...",
  "transactionHash": "0xabc...",
  "blockNumber": 12345678,
  "blockHash": "0xdef4567890abcdef...",
  "contractAddress": "0xClosureAnchor...",
  "l2Chain": "eip155:8453",
  "timestamp": "2025-03-22T10:00:00",
  "anchorer": "0xYourAddress...",
  "status": "confirmed"
}