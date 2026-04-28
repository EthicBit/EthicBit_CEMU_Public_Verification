# Auditing EthicBit/CEMU L5

This document is the formal audit guide for the L5 constitutional evidence
ceiling of EthicBit/CEMU. Any external auditor — without private keys,
without prior context, without maintainer cooperation — can independently
verify or falsify every claim the system makes, in approximately 30 seconds.

## Quick falsification

```sh
git clone https://github.com/EthicBit/EthicBit_CEMU
cd EthicBit_CEMU
pip install eth_account
python3 scripts/core/verify_l5_full_chain.py
python3 scripts/core/test_tampering_resistance.py
```

Both commands must return exit code `0`. Any non-zero exit refutes the
corresponding claim.

## What the system claims (verifiable)

### C1 — Real EIP-4844 blob anchor on Sepolia

Latest TX: `0xfb1f2246f2064e6064a4b50e5f3f4d18c697229a819e52057114f505e0b3f13b`,
block `10742400`. Previous: `0xbf603bf0...e70`, block `10732589`.

**Falsify**: query any public Sepolia RPC for either tx_hash. STAGE 3 of
`verify_l5_full_chain.py` does this against 4 RPCs and asserts type=0x3,
blobVersionedHashes match, receipt.status=1.

Browser: https://sepolia.etherscan.io/tx/0xfb1f2246f2064e6064a4b50e5f3f4d18c697229a819e52057114f505e0b3f13b

### C2 — Cryptographic chain of custody

The wallet that signed the ceiling JSON also sent the blob TX:
`0x9221456deCC27547aA76EC5d53537dfe430C69B7`.

**Falsify**: run `verify_ceiling_signature.py`. It recovers the address
from the EIP-191 signature on the canonical ceiling JSON and asserts
equality with `tx.from`. Address mismatch breaks the chain.

### C3 — Anti-tampering on local JSONs

Modifying `tx_hash`, `from_address`, or `block_number` in
`results/kzg_blob_anchor_report.json` is detected.

**Falsify**: run `test_tampering_resistance.py`. It executes 3 distinct
attack classes (inexistence, wrong-from, wrong-block); each must be
detected and the system must recover to PASS after restoration.

### C4 — Constitutional contract satisfied

13 controls in `config/constitutional_controls.v1.json`.

**Falsify**: run

```sh
ETHICBIT_ME_GATE_REQUIRED_SECTORS="CORE,JUSTICIA,FINANZAS,SECURITY,TECHNICAL,LEGAL,REGULATORY" \
bash scripts/audit/verify_constitutional_controls.sh
```

Expect: `total=13 pass=13 fail=0 must_fail=0` and
`CONSTITUTIONAL_STATUS=PASS`.

## What the system does NOT claim

These are deliberate limits. Any reading that exceeds them is unsupported.

- **Not legally binding on third parties.** Technical closure is not
  doctrinal closure. Judges, regulators, and sovereign authorities are
  not automatically bound by internal validation.
- **Not on mainnet.** All anchors are on Sepolia testnet (no economic
  value). Mainnet migration is a separate decision.
- **`confidence` is hardcoded** at `0.928`. Acceptable per current gates,
  flagged as technical debt.
- **Single-key custody.** Wallet `0x9221456d...` is single-key, not
  multi-sig. Key compromise compromises issuance of new anchors.
- **External RPC dependency.** STAGE 3 needs at least one of 4 public
  RPCs (drpc, 1rpc, tenderly, publicnode) to be reachable.

## Verifier reference

| Command | Checks | Pass exit |
|---|---|---|
| `scripts/core/verify_l5_full_chain.py` | All 3 stages | 0 |
| `scripts/core/verify_l5_canonical_state.py` | Stage 1 only (offline) | 0 |
| `scripts/core/verify_ceiling_signature.py` | Stage 2 only (crypto) | 0 |
| `scripts/core/verify_l5_onchain.py` | Stage 3 only (on-chain) | 0 |
| `scripts/core/test_tampering_resistance.py` | 3 attack classes | 0 |
| `scripts/audit/verify_constitutional_controls.sh` | 13 controls | 0 |

### CI badge

Live result on every commit to main, green = passing, red = failing.
Visible at https://github.com/EthicBit/EthicBit_CEMU.

## Re-anchor procedure (maintainer only)

```sh
python3 scripts/core/reanchor_blob_sepolia.py
```

Requires `ETHICBIT_PRIVATE_KEY` in `.env`, ~0.0004 SepoliaETH balance,
and network access. The only operation that needs the key. All
verification is read-only and key-free.

## Troubleshooting

**`STAGE 3 FAIL: no RPC could confirm`** — all 4 RPCs unreachable.
Retry in 5 min, or configure a private endpoint (Alchemy free tier).

**`STAGE 2 FAIL: recovered != claimed signer`** — ceiling content
changed without re-signing. Run re-anchor.

**`CTL-EV-001 FAIL: claim_level=NONE`** — run
`python3 scripts/core/constitutional_evidence_ceiling_gate.py` to
regenerate the ceiling.

## Anchor history

| # | TX hash | Block | Notes |
|---|---|---|---|
| 1 | `0xbf603bf0...e70` | 10732589 | Original anchor |
| 2 | `0xfb1f2246...3f13b` | 10742400 | Refresh 1 (~33h later) |

Multiple anchors over time demonstrate continuous on-chain liveness.

## Schema reference

### `results/kzg_blob_anchor_report.json` (required keys)

- `schema_id: "ETHICBIT_KZG_BLOB_ANCHOR_V1"`
- `status: "ONCHAIN_BLOB_ANCHOR_VERIFIED"`
- `tx_hash`, `chain_id: 11155111`, `tx_type: "0x3"`
- `block_number`, `from_address`
- `blob_versioned_hashes` (each with `0x01` prefix)

### `results/constitutional_evidence_ceiling.sig` (required keys)

- `schema_id: "ETHICBIT_CEILING_SIGNATURE_V1"`
- `scheme: "EIP-191_personal_sign"`
- `canonicalization: "json_sort_keys_no_whitespace_utf8"`
- `signature`, `signer_address`, `message_hash`

## Reporting refutations

If any verification command returns non-zero exit, please file an issue
at https://github.com/EthicBit/EthicBit_CEMU/issues with the command
run, the exit code, and the full output. Successful refutation is
valuable evidence and not a hostile act.

## Last verified

This document is metadata. The code is the source of truth — re-run
the verifier locally for ground truth at any time.
