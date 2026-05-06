# Agente Etico Mecanico - Definicion Canonica V1.1

**EthicBit/CEMU**

- Version: 1.1
- Fecha de definicion canonica: 2026-04-30
- Estado del documento: PUBLIC_CANONICAL_DEFINITION
- Schema id: ETHICBIT_AEM_DEFINITION_V1_1
- Estado verificable asociado: PUBLIC_L5_AEM_VERIFICATION_PASS

---

## 1. Proposito

Este documento fija la definicion canonica V1.1 de la categoria
**Agente Etico Mecanico** (AEM) dentro de la arquitectura EthicBit/CEMU.

V1.0 (2026-04-28) permanece inalterada como evidencia historica de la
primera demostracion publica reproducible del patron AEM. Esta V1.1
extiende la definicion con una octava propiedad estructural:
**deterministic pre-execution gating por snapshot inheritance**.

## 2. Definicion canonica V1.1

Un **Agente Etico Mecanico** (AEM) es un sistema computacional que
satisface simultaneamente, al momento de su atestacion publica,
las siguientes ocho propiedades verificables por terceros sin acceso a
claves privadas, sin cooperacion del operador y en tiempo finito.

### 2.1 Operacion bajo Mechanical Ethics

Verificacion:

    bash scripts/audit/verify_constitutional_controls.sh

Pass condition:

- CONSTITUTIONAL_STATUS=PASS
- Baseline vigente: total=14 pass=14 fail=0 must_fail=0

### 2.2 Estado constitucional verificable

Verificacion:

    scripts/core/verify_l5_canonical_state.py
    scripts/core/verify_l5_full_chain.py

Pass condition:

- claim_level_ceiling=L5
- L5_CANONICAL_STATE=PASS
- L5_FULL_CHAIN=PASS

### 2.3 Cadena de custodia criptografica

Verificacion:

    python3 scripts/core/verify_ceiling_signature.py

Pass condition:

- recovered_address == claimed_signer == anchor.from_address
- CHAIN_OF_CUSTODY=VERIFIED

### 2.4 Anclaje en infraestructura publica independiente

Verificacion:

    python3 scripts/core/verify_l5_onchain.py

Pass condition:

- tipo de transaccion = 0x3 (EIP-4844 blob)
- from_address consistente con la cadena de custodia
- receipt.status=success
- ONCHAIN_CROSS_VERIFICATION=PASS

### 2.5 Anti-tampering empiricamente probado

Verificacion:

    python3 scripts/core/test_tampering_resistance.py

Pass condition:

- 3 attack classes detectadas: inexistence, wrong-from, wrong-block
- fail-closed bajo ataque
- recuperacion a estado PASS tras restauracion
- TAMPERING_RESISTANCE=PROVEN

### 2.6 Falsificabilidad publica en tiempo finito

Verificacion consolidada:

    python3 scripts/core/master_closure_orchestrator.py --mode public-verify --with-tampering-test

Pass condition:

- MASTER_CLOSURE_STATUS=PASS
- modo public-verify (sin firma nueva, sin anclaje nuevo, sin mutacion)

### 2.7 Delimitacion explicita frente a terceros

Verificacion:

    results/master_closure_report.json
    docs/third_party_representation_boundary.md

Pass condition:

- summary.third_party_binding=false
- summary.third_party_presentability=READY_WITH_SCOPE_DELIMITATION

### 2.8 Deterministic pre-execution gating con snapshot inheritance

La operacion de bucle rapido no recalcula en cada tick el aparato
probatorio completo. En su lugar, hereda validez constitucional desde
un snapshot L5 vigente y ejecuta guardias de pre-ejecucion
fail-closed antes de permitir continuidad operativa.

Evidencia empirica actual:

- `results/realtime_daemon_probe_report.json`
  - mode=REALTIME_DAEMON_10MS_PROBE
  - status=PASS
  - ticks_total=409
  - ticks_ok=409
  - ticks_blocked=0
  - interval_ms=10
  - fail_closed_policy=true
- `results/realtime_millisecond_guard.json`
  - mode=REALTIME_10MS_COMPATIBLE
  - guard=OK
  - snapshot_status=PASS
  - constitutional_equivalence=true
  - fingerprint_valid=true
  - claim_level_ceiling=L5

Pass condition:

- pre-execution guard en PASS
- snapshot inheritance constitucional valida
- fail-closed disponible ante deriva o incoherencia

## 3. Criterios verificables consolidados

| # | Propiedad | Evidencia principal | Pass condition |
|---|---|---|---|
| 1 | Mechanical Ethics | `scripts/audit/verify_constitutional_controls.sh` | 14/14 PASS |
| 2 | Estado constitucional | `scripts/core/verify_l5_canonical_state.py` | L5_CANONICAL_STATE=PASS |
| 3 | Cadena de custodia | `scripts/core/verify_ceiling_signature.py` | CHAIN_OF_CUSTODY=VERIFIED |
| 4 | Anclaje on-chain | `scripts/core/verify_l5_onchain.py` | ONCHAIN_CROSS_VERIFICATION=PASS |
| 5 | Full chain L5 | `scripts/core/verify_l5_full_chain.py` | L5_FULL_CHAIN=PASS |
| 6 | Anti-tampering | `scripts/core/test_tampering_resistance.py` | TAMPERING_RESISTANCE=PROVEN |
| 7 | Verificacion publica | `scripts/core/master_closure_orchestrator.py` | MASTER_CLOSURE_STATUS=PASS |
| 8 | Pre-execution gating | `results/realtime_daemon_probe_report.json` + `results/realtime_millisecond_guard.json` | guard PASS + snapshot inheritance valida |

## 4. Clausula de prioridad temporal (matizada)

La expresion "primer Agente Etico Mecanico" se formula en sentido
tecnico-probatorio y debe leerse asi:

> Segun evidencia publica reproducible disponible y to our knowledge, el
> sistema identificado en EthicBit/CEMU constituye la primera
> atestacion publica reproducible de la categoria AEM bajo esta
> definicion canonica, salvo evidencia material anterior equivalente.

Esta formula:

- no afirma primacia ontologica absoluta;
- no implica reconocimiento juridico automatico por terceros soberanos;
- permanece falsificable por evidencia material anterior equivalente.

## 5. Atestacion material (modelo canonic + receipt separado)

Este documento define la categoria. El anchor material se registra en
un artifact separado de receipt para preservar inmutabilidad del
canonic.

Receipt objetivo para V1.1:

- `docs/anchors/AEM_V1_1_MAINNET_ANCHOR_RECEIPT.json`

El receipt, una vez emitido, debera contener como minimo:

- network
- chain_id
- tx_hash
- block_number
- timestamp_utc
- signer_address
- definition_sha256 (de este canonic V1.1)
- thesis_sha256
- system_state_sha256
- repo_commit_sha

Hasta que exista el receipt mainnet, este documento mantiene
estado canonic publicable con evidencia tecnica reproducible.

## 6. Trazabilidad y estado tecnico al 2026-04-30

Corrida de referencia reciente:

- mode=public-verify
- MASTER_CLOSURE_STATUS=PASS
- constitutional_status=PASS
- claim_level_ceiling=L5
- anti_re_status=PASS
- TAMPERING_RESISTANCE=PROVEN
- third_party_binding=false
- third_party_presentability=READY_WITH_SCOPE_DELIMITATION

Anchor tecnico historico (V1.0):

- network=Sepolia testnet
- tx_hash=0xfb1f2246f2064e6064a4b50e5f3f4d18c697229a819e52057114f505e0b3f13b
- block_number=10742400

## 7. Cierre formal

Este documento constituye la definicion canonica AEM V1.1.
Su SHA-256 sobre UTF-8 del archivo congelado es su identificador
inmutable para trazabilidad documental.

Cualquier cambio sustantivo posterior debera emitirse como nueva
version, sin invalidar la evidencia historica de V1.0 ni V1.1.

## 8. Runtime Secret Protection Posture

AEM V1.1 includes ML-KEM768 + X25519 hybrid runtime secret protection for Mechanical Ethics, with HKDF-derived hybrid secrets, fail-closed behavior, and non-sensitive canonical metadata recording.

Implementation and posture reference:

- `assurance/crypto/pq_kem.go`
- `mechanical_ethics/gate.go`
- `docs/crypto/MLKEM768_RUNTIME_SECRET_PROTECTION.md`
- `results/pq_runtime_secret_protection.json`

This posture relies on NIST FIPS 203 ML-KEM assumptions and does not claim FIPS module validation, cryptographic module certification, absolute quantum security, production cryptographic certification, third-party cryptographic certification, regulatory approval, SLSA L4 cryptographic closure, clinical validation, or diagnostic authorization.
