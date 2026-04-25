#!/usr/bin/env python3
"""Constitutional Evidence Ceiling Gate — V2 (L4 floor + L5 ceiling).

Diseño:
  - L4 floor: 6 chequeos LOCALES e INDEPENDIENTES (no se delega a upstream).
  - L5 ceiling: solo accesible si L4 esta firme. Requiere:
      * 5 fuentes presentes (incluida chainlink_external)
      * Chainlink evidence con liveness confirmado
      * KZG blob anchor verificado on-chain (Sepolia type-3 TX)
  - Audit trail completo: schema, timestamp, todos los campos originales.
  - Idempotente y resistente a archivos faltantes.
"""
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "constitutional_evidence_ceiling.json"
RUNTIME = ROOT / "results" / "runtime_evidence_strength_report.json"
ME_GATE = ROOT / "results" / "mechanical_ethics_gate.json"
KZG_REPORT = ROOT / "results" / "l5_onchain_anchor_report.json"
CHAINLINK_EVIDENCE = ROOT / "results" / "chainlink_evidence.json"

# L5 requiere las 4 fuentes L4 mas un oraculo independiente (chainlink)
REQUIRED_L5_SOURCES = {
    "real_local",
    "arweave_external",
    "sepolia_external",
    "pyth_external",
    "chainlink_external",
}


def now():
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


runtime = load_json(RUNTIME) or {}
me_gate = load_json(ME_GATE) or {}
kzg = load_json(KZG_REPORT)
chainlink = load_json(CHAINLINK_EVIDENCE)

# ============================================================
# L4 FLOOR — 6 chequeos locales (computo independiente)
# ============================================================
confidence = float(runtime.get("confidence", 0.0) or 0.0)
evidence_mode = str(runtime.get("evidence_mode", "UNKNOWN"))
health_score = str(runtime.get("health_score", "UNKNOWN"))
real_sources_used = runtime.get("real_sources_used") or runtime.get("sources") or []
mechanical_ethics_status = str(runtime.get("mechanical_ethics_status", "UNKNOWN"))
runtime_reasons = runtime.get("reasons") or []
positive_evidence_count = sum(
    1 for r in runtime_reasons
    if isinstance(r, str)
    and any(t in r for t in ("VERIFIED", "ANCHOR_ACTIVE", "PASS", "CONFIRMED", "ATTESTED"))
)

reasons = []

if mechanical_ethics_status != "PASS":
    reasons.append("MECHANICAL_ETHICS_NOT_PASS")

if positive_evidence_count < 4:
    reasons.append("POSITIVE_EVIDENCE_BELOW_4(got=" + str(positive_evidence_count) + ")")

if len(real_sources_used) < 2:
    reasons.append("NO_SUFFICIENT_REAL_SOURCES_FOR_L4")

if confidence < 0.85:
    reasons.append("CONFIDENCE_BELOW_L4_THRESHOLD")

if health_score == "SIMULATED":
    reasons.append("HEALTH_SCORE_SIMULATED")

if evidence_mode in {"SELF_ATTESTED_FALLBACK", "SELF_ATTESTED_ONLY", "UNKNOWN"}:
    reasons.append("SELF_ATTESTED_ONLY_NOT_ALLOWED_FOR_L4_PLUS")

eligible_for_l4 = len(reasons) == 0

# ============================================================
# L5 CEILING — solo accesible si L4 esta firme
# ============================================================
sources_present = set(runtime.get("sources", []) or [])
missing_l5_sources = sorted(REQUIRED_L5_SOURCES - sources_present)
l5_reasons = []

if missing_l5_sources:
    l5_reasons.append("L5_MISSING_SOURCES:" + ",".join(missing_l5_sources))

if chainlink is None:
    l5_reasons.append("L5_CHAINLINK_EVIDENCE_MISSING")
elif not chainlink.get("liveness_confirmed", False):
    l5_reasons.append("L5_CHAINLINK_LIVENESS_NOT_CONFIRMED")

if kzg is None:
    l5_reasons.append("L5_KZG_ANCHOR_REPORT_MISSING")
else:
    kzg_status = str(kzg.get("status") or "UNKNOWN")
    kzg_verification_status = str(kzg.get("verification_status") or "UNKNOWN")
    kzg_blob_versioned_hash = (
        kzg.get("blob_versioned_hash")
        or (kzg.get("blob_versioned_hashes")[0] if isinstance(kzg.get("blob_versioned_hashes"), list) and kzg.get("blob_versioned_hashes") else None)
    )

    if kzg_status != "PASS":
        l5_reasons.append("L5_KZG_STATUS_NOT_PASS")

    if kzg_verification_status != "ONCHAIN_KZG_BLOB_VERIFIED":
        l5_reasons.append("L5_KZG_VERIFICATION_STATUS_NOT_CONFIRMED")

    if not kzg_blob_versioned_hash:
        l5_reasons.append("L5_KZG_BLOB_VERSIONED_HASH_MISSING")

eligible_for_l5 = eligible_for_l4 and len(l5_reasons) == 0

current_ceiling = runtime.get("claim_level_ceiling", "L1")
if eligible_for_l5:
    current_ceiling = "L5"
elif eligible_for_l4:
    current_ceiling = "L4"

status = "PASS" if eligible_for_l4 else "FAIL_CLOSED"

# ============================================================
# REPORT — audit trail completo
# ============================================================
report = {
    "schema_id": "ETHICBIT_CONSTITUTIONAL_EVIDENCE_CEILING_V2_1",
    "generated_at": now(),
    "status": status,
    "mechanical_ethics_status": mechanical_ethics_status,
    "current_ceiling": current_ceiling,
    "claim_level_ceiling": current_ceiling,
    "target_ceiling": "L5",
    "eligible_for_l4": eligible_for_l4,
    "eligible_for_l5": eligible_for_l5,
    "evidence_mode": evidence_mode,
    "confidence": confidence,
    "health_score": health_score,
    "positive_evidence_count": positive_evidence_count,
    "real_sources_used": real_sources_used,
    "sources": sorted(sources_present),
    "missing_l5_sources": missing_l5_sources,
    "reasons": reasons,
    "l5_reasons": l5_reasons,
    "kzg_anchor": {
        "report_present": kzg is not None,
        "status": kzg.get("status") if kzg else None,
        "tx_hash": kzg.get("tx_hash") if kzg else None,
        "block_number": kzg.get("block_number") if kzg else None,
        "blob_versioned_hash": (kzg.get("blob_versioned_hash") or (kzg.get("blob_versioned_hashes")[0] if isinstance(kzg.get("blob_versioned_hashes"), list) and kzg.get("blob_versioned_hashes") else None)) if kzg else None,
        "blob_versioned_hashes": kzg.get("blob_versioned_hashes") if kzg else None,
    },
    "chainlink_evidence": {
        "report_present": chainlink is not None,
        "liveness_confirmed": chainlink.get("liveness_confirmed") if chainlink else None,
        "feed": chainlink.get("feed") if chainlink else None,
        "price": chainlink.get("price") if chainlink else None,
        "age_seconds": chainlink.get("age_seconds") if chainlink else None,
    },
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print(f"constitutional_evidence_ceiling={OUT}")
print(f"status={status}")
print(f"current_ceiling={current_ceiling}")
print(f"eligible_for_l4={eligible_for_l4}")
print(f"eligible_for_l5={eligible_for_l5}")
if reasons:
    print("reasons=" + ",".join(reasons))
if l5_reasons:
    print("l5_reasons=" + ",".join(l5_reasons))
