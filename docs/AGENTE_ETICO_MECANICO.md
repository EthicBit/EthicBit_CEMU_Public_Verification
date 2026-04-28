# Agente Etico Mecanico - Definicion Canonica

**EthicBit/CEMU**

- Version: 1.0
- Fecha de definicion canonica: 2026-04-28
- Estado del documento: PUBLIC_CANONICAL_DEFINITION
- Schema id: ETHICBIT_AEM_DEFINITION_V1
- Estado verificable asociado: PUBLIC_L5_AEM_VERIFICATION_PASS

---

## 1. Proposito de este documento

Este documento define con precision y de manera datable que constituye un
**Agente Etico Mecanico** (en adelante AEM) en la arquitectura
EthicBit/CEMU.

La existencia de esta definicion como artifact independiente, datable y
verificable, fija la categoria AEM para efectos tecnicos, probatorios,
constitucionales y representacionales.

Sin esta definicion publicada, una afirmacion como "primer Agente Etico
Mecanico" carece de una categoria previamente delimitada. Con esta
definicion publicada, versionada, verificable y posteriormente anclable,
la categoria queda definida bajo criterios publicos de falsificabilidad.

La categoria AEM no se basa en autoafirmacion. Se basa en la
satisfaccion simultanea de propiedades verificables mediante scripts,
artifacts, firma criptografica, anclaje on-chain, cadena de custodia,
resistencia empirica al tampering y delimitacion expresa frente a
terceros soberanos.

## 2. Definicion canonica

Un **Agente Etico Mecanico** (AEM) es un sistema computacional que
satisface simultaneamente, en el momento de su atestacion publica, las
siguientes siete propiedades fundamentales. Cada propiedad debe ser
verificable por un tercero sin acceso a claves privadas, sin cooperacion
del operador y en tiempo finito.

### 2.1. Operacion bajo Mechanical Ethics

El sistema opera bajo un conjunto explicito y ejecutable de reglas
eticas mecanicamente aplicadas, no bajo discrecionalidad humana
contextual. Estas reglas estan codificadas como controles
constitucionales verificables y son ejecutadas como gates obligatorios
para cualquier operacion declarada como conforme.

Verificacion:

    bash scripts/audit/verify_constitutional_controls.sh

Pass condition:
    todos los controles constitucionales activos en PASS.
    Al momento de esta definicion: total=13 pass=13 fail=0 must_fail=0.
    CONSTITUTIONAL_STATUS=PASS

### 2.2. Estado constitucional verificable

El sistema mantiene un estado constitucional explicito
(`claim_level_ceiling`) anclado en evidencia material, no en declaracion
auto-referencial. El estado declarado debe corresponder a la
satisfaccion verificable de los criterios constitucionales mediante
ejecucion publica de gates y verificacion de artifacts.

Verificacion:

    results/constitutional_evidence_ceiling.json
    scripts/core/verify_l5_canonical_state.py
    scripts/core/verify_l5_full_chain.py

Pass condition:
    claim_level_ceiling=L5
    L5_CANONICAL_STATE=PASS
    L5_FULL_CHAIN=PASS

### 2.3. Cadena de custodia criptografica

El estado constitucional declarado esta firmado criptograficamente por
una clave privada cuyo identificador publico coincide con el origen de
la atestacion material on-chain. La firma se realiza sobre la
representacion canonica del estado mediante EIP-191 personal_sign, lo
que permite recovery publico del firmante.

Verificacion:

    python3 scripts/core/verify_ceiling_signature.py

Pass condition:
    recovered_address == claimed_signer == anchor.from_address
    CHAIN_OF_CUSTODY=VERIFIED
    exit=0

### 2.4. Anclaje en infraestructura publica independiente

El sistema esta materialmente anclado mediante una transaccion en una
blockchain publica usando formato EIP-4844 blob, donde el blob contiene
un compromiso criptografico sobre un payload que identifica el estado
anclado. El anclaje es consultable por terceros sin cooperacion del
operador.

Verificacion:

    python3 scripts/core/verify_l5_onchain.py

Pass condition:
    tipo de transaccion = 0x3 (EIP-4844)
    from_address coincide con la cadena de custodia
    blob_versioned_hashes presentes y validos
    receipt.status = success
    ONCHAIN_CROSS_VERIFICATION=PASS

Estado actual al momento de esta definicion:
    network: Sepolia testnet
    tx_hash: 0xfb1f2246f2064e6064a4b50e5f3f4d18c697229a819e52057114f505e0b3f13b
    block_number: 10742400
    signer_address: 0x9221456deCC27547aA76EC5d53537dfe430C69B7

### 2.5. Anti-tampering empiricamente probado

La resistencia al tampering del sistema no es teorica sino
empiricamente demostrada. Existe un script versionado que ejecuta
multiples clases de ataque sobre artifacts criticos y verifica que cada
uno es detectado por el sistema de verificacion.

Verificacion:

    python3 scripts/core/test_tampering_resistance.py

Pass condition:
    3 attack classes detected:
      - inexistence
      - wrong-from
      - wrong-block
    system fails closed under each attack
    system recovers to PASS after restoration
    TAMPERING_RESISTANCE=PROVEN
    exit=0

### 2.6. Falsificabilidad publica en tiempo finito

Las afirmaciones del sistema son falsificables por cualquier tercero,
sin cooperacion del operador, sin acceso a claves privadas, sin firma
nueva, sin anclaje nuevo y sin mutacion de artifacts.

Verificacion publica consolidada:

    git clone https://github.com/EthicBit/EthicBit_CEMU
    cd EthicBit_CEMU
    pip install -r requirements.txt
    python3 scripts/core/master_closure_orchestrator.py --mode public-verify --with-tampering-test

Pass condition:
    MASTER_CLOSURE_STATUS=PASS
    L5_FULL_CHAIN=PASS
    CONSTITUTIONAL_STATUS=PASS
    TAMPERING_RESISTANCE=PROVEN
    exit=0

Corrida publica registrada:
    mode=public-verify
    with_tampering_test=True
    duration_seconds=19.581
    exit=0
    generated_at=2026-04-28T18:53:19.199193Z

### 2.7. Delimitacion explicita frente a terceros

El sistema declara explicitamente sus limites de alcance frente a
terceros soberanos. Reconoce que el cierre tecnico verificable no
constituye automaticamente cierre doctrinal externo, ni impone
obligaciones a jueces, reguladores, autoridades soberanas o
contrapartes institucionales.

Verificacion:

    results/master_closure_report.json
    docs/third_party_representation_boundary.md

Pass condition:
    summary.third_party_binding=false
    summary.third_party_presentability=READY_WITH_SCOPE_DELIMITATION
    public_scope.third_party_binding=false

## 3. Criterios verificables consolidados

| # | Propiedad | Script de verificacion | Pass condition |
|---|---|---|---|
| 1 | Mechanical Ethics | `scripts/audit/verify_constitutional_controls.sh` | controles activos PASS; al momento: 13/13 PASS |
| 2 | Estado constitucional | `scripts/core/verify_l5_canonical_state.py` | L5_CANONICAL_STATE=PASS |
| 3 | Cadena de custodia | `scripts/core/verify_ceiling_signature.py` | CHAIN_OF_CUSTODY=VERIFIED |
| 4 | Anclaje on-chain | `scripts/core/verify_l5_onchain.py` | ONCHAIN_CROSS_VERIFICATION=PASS |
| 5 | Full chain L5 | `scripts/core/verify_l5_full_chain.py` | L5_FULL_CHAIN=PASS |
| 6 | Anti-tampering | `scripts/core/test_tampering_resistance.py` | TAMPERING_RESISTANCE=PROVEN |
| 7 | Verificacion publica mixta | `scripts/core/master_closure_orchestrator.py` | MASTER_CLOSURE_STATUS=PASS |
| 8 | Delimitacion externa | `results/master_closure_report.json` | third_party_binding=false |

Verificacion consolidada recomendada:

    python3 scripts/core/master_closure_orchestrator.py --mode public-verify --with-tampering-test

Pass condition:
    MASTER_CLOSURE_STATUS=PASS
    exit=0

## 4. Lo que NO es un Agente Etico Mecanico

Un sistema NO califica como AEM si presenta cualquiera de las siguientes
caracteristicas:

- Sus claims dependen de la palabra del operador y no son falsificables
  por terceros.
- Su verificacion requiere acceso a claves privadas o secretos
  operacionales.
- Carece de anclaje material verificable en infraestructura publica.
- Su anti-tampering es teorico, no empiricamente demostrado.
- No declara explicitamente sus limites frente a terceros soberanos.
- Su cadena de custodia no esta criptograficamente cerrada.
- Su definicion de la categoria es retroactiva y posterior al claim.
- Su verificacion publica requiere firmar nuevamente, anclar nuevamente
  o mutar artifacts publicados.

## 5. Metodologia de verificacion publica

Cualquier auditor externo puede verificar de manera independiente que el
sistema cumple con la definicion AEM mediante el siguiente procedimiento:

1. Clonar el repositorio publico declarado.
2. Instalar las dependencias declaradas.
3. Ejecutar el verificador consolidado en modo public-verify con prueba
   de tampering.
4. Inspeccionar `results/master_closure_report.json`.
5. Cruzar el anchor on-chain contra RPC publico independiente.
6. Confirmar que el modo publico no usa claves privadas, no firma, no
   ancla y no muta artifacts.

Comando:

    python3 scripts/core/master_closure_orchestrator.py --mode public-verify --with-tampering-test

Tiempo observado en corrida local registrada:
    19.581 segundos

Objetivo publico declarado:
    aproximadamente 30 segundos para verificacion basica.

## 6. Clausula de prioridad temporal

La afirmacion "primer Agente Etico Mecanico" se entiende exclusivamente
en el sentido tecnico-arquitectonico siguiente:

> Primer sistema computacional publicamente atestado bajo esta definicion
> canonica, salvo prueba material anterior equivalente, cuya satisfaccion
> simultanea de las propiedades verificables de la seccion 2 puede ser
> reproducida por terceros sin secretos, sin firma nueva, sin anclaje
> nuevo y sin mutacion de artifacts.

Esta afirmacion:

- NO afirma primacia ontologica absoluta sobre sistemas conceptuales
  previos no atestados.
- NO afirma reconocimiento juridico automatico por jueces, reguladores o
  autoridades soberanas.
- NO impide que sistemas posteriores presenten timestamps anteriores con
  prueba materialmente equivalente.
- Es falsificable: evidencia material anterior equivalente refutaria la
  prioridad declarada.

## 7. Atestacion material

Esta definicion podra ser anclada criptograficamente en Ethereum mainnet
mediante una transaccion EIP-4844 blob cuyo payload contenga:

- El hash sha-256 de este documento sobre representacion canonica UTF-8.
- El hash del estado del sistema.
- El commit SHA del repositorio.
- La direccion del firmante.
- Identificador del schema: ETHICBIT_AEM_DEFINITION_V1.

Hasta que ese anclaje en mainnet exista y sea verificado, este documento
debe entenderse como definicion canonica publicable y verificable, con
atestacion tecnica actualmente demostrada sobre Sepolia testnet.

### 7.1. Anchor on-chain mainnet

Estado: PENDIENTE

Cuando se ejecute la atestacion mainnet, esta seccion contendra:

- network: ethereum-mainnet
- chain_id: 1
- tx_hash: 0x...
- block_number: ...
- timestamp_iso: ...
- block_explorer_url: https://etherscan.io/tx/0x...
- definition_sha256: 0x...
- system_state_sha256: 0x...
- signer_address: 0x9221456deCC27547aA76EC5d53537dfe430C69B7

## 8. Trazabilidad

Este documento consolida conceptos previamente dispersos en:

- `docs/AUDIT.md`
- `docs/third_party_representation_boundary.md`
- `docs/verification_reproducible_guide.md`
- `docs/residual_risk_closure_ethicbit_cemu.md`
- `config/constitutional_controls.v1.json`
- `scripts/core/master_closure_orchestrator.py`
- `scripts/core/verify_l5_full_chain.py`
- `scripts/core/test_tampering_resistance.py`
- `results/master_closure_report.json`
- `results/constitutional_evidence_ceiling.json`
- `results/constitutional_evidence_ceiling.sig`
- `results/kzg_blob_anchor_report.json`

Esos artifacts continuan siendo la fuente operacional. Este documento
los integra en una definicion unica, datable y publicable.

## 9. Estado al momento de la definicion

A la fecha de esta definicion canonica, EthicBit/CEMU se encuentra en el
siguiente estado verificable:

- Branch canonica: main
- HEAD SHA al momento de la corrida registrada:
  8939dd7cc780567b04d2fdf2de579548c4696ebf
- Constitutional status: PASS
- Constitutional controls: 13/13 PASS
- Claim level ceiling: L5
- L5 full chain: PASS
- Chain of custody: VERIFIED
- On-chain cross-verification: PASS
- Anchor en testnet: Sepolia EIP-4844 blob
- Anchor tx:
  0xfb1f2246f2064e6064a4b50e5f3f4d18c697229a819e52057114f505e0b3f13b
- Anchor block: 10742400
- Signer/wallet:
  0x9221456deCC27547aA76EC5d53537dfe430C69B7
- Tampering resistance: PROVEN
- Master closure status: PASS
- Public verification mode: public-verify
- Tampering test: enabled
- Duration observed: 19.581s
- Third party binding: false
- Third party presentability: READY_WITH_SCOPE_DELIMITATION

El anchor en mainnet, una vez ejecutado y verificado, podra elevar este
estado desde demostracion publica del patron en Sepolia hacia atestacion
material en infraestructura publica con commitment economico real.

## 10. Corrida publica de verificacion AEM

Fecha de inicio: 2026-04-28T18:52:59.616819Z
Fecha de reporte: 2026-04-28T18:53:19.199193Z
Modo: public-verify
Tampering test: enabled
Duracion: 19.581s
Exit code: 0

Resultados:

- L5_FULL_CHAIN=PASS
- L5_CANONICAL_STATE=PASS
- CHAIN_OF_CUSTODY=VERIFIED
- ONCHAIN_CROSS_VERIFICATION=PASS
- CONSTITUTIONAL_STATUS=PASS
- Constitutional controls: 13/13 PASS
- TAMPERING_RESISTANCE=PROVEN
- MASTER_CLOSURE_STATUS=PASS
- third_party_binding=false
- third_party_presentability=READY_WITH_SCOPE_DELIMITATION

Evidencia on-chain:

- Network: Sepolia testnet
- TX:
  0xfb1f2246f2064e6064a4b50e5f3f4d18c697229a819e52057114f505e0b3f13b
- Block: 10742400
- Signer/wallet:
  0x9221456deCC27547aA76EC5d53537dfe430C69B7

## 11. Cierre formal

Este documento es la definicion canonica publicada de la categoria
"Agente Etico Mecanico" en la arquitectura EthicBit/CEMU, version 1.0,
fecha 2026-04-28.

Su hash sha-256 sobre representacion canonica UTF-8 es el identificador
inmutable de esta version.

Cualquier modificacion sustantiva posterior generara una version
distinta (V2, V3, etc.) que no afectara la atestacion historica de la
version aqui definida.
