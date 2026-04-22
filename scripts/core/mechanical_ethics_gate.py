#!/usr/bin/env python3
"""Canonical Mechanical Ethics gate with REAL_LOCAL evidence."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.core.RegistryManager import RegistryManager  # noqa: E402
from scripts.core.real_local_evidence import resolve_required_evidence  # noqa: E402


DEFAULT_SECTORS = [
    "CORE",
    "JUSTICIA",
    "FINANZAS",
    "SECURITY",
    "TECHNICAL",
    "LEGAL",
    "REGULATORY",
]
L4_FOUNDATIONAL_SECTORS = [
    "CORE",
    "TECHNICAL",
    "SECURITY",
    "LEGAL",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_csv(value: str) -> List[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


async def evaluate_gate(
    manager: RegistryManager,
    sectors: List[str],
) -> Dict[str, Any]:
    per_rule: List[Dict[str, Any]] = []
    per_sector: Dict[str, Dict[str, Any]] = {}

    for sector in sectors:
        manager._ensure_sector_loaded(sector)
        rules = [
            rule
            for rule in manager.registries.get(sector, {}).get("rules", [])
            if rule.get("severity") == "CRITICAL"
        ]

        sector_records: List[Dict[str, Any]] = []
        sector_missing: List[str] = []
        for rule in rules:
            required = manager._normalize_required_evidence(rule)
            evidence, missing, resolver_trace = resolve_required_evidence(required, ROOT)
            state = {
                "audit": {"canonical": True},
                "evidence": {"resolver_mode": "REAL_LOCAL"},
                "real_local_evidence": evidence,
            }
            result = await manager.evaluate_async(
                rule_id=rule["rule_id"],
                state=state,
                extra_evidence=evidence,
                sector=sector,
            )
            entry = asdict(result)
            entry["resolver"] = {
                "mode": "REAL_LOCAL",
                "missing": missing,
                "trace": resolver_trace,
            }
            sector_records.append(entry)
            per_rule.append(entry)
            if missing:
                sector_missing.extend(missing)

        sector_status = "PASS"
        if not rules:
            sector_status = "UNSUPPORTED"
        elif any(record["status"] != "PASS" for record in sector_records):
            sector_status = "FAIL_CLOSED"

        per_sector[sector] = {
            "status": sector_status,
            "critical_rule_count": len(rules),
            "failed_rules": [
                record["ruleId"]
                for record in sector_records
                if record["status"] != "PASS"
            ],
            "missing_evidence_keys": sorted(set(sector_missing)),
        }

    return {
        "per_sector": per_sector,
        "per_rule": per_rule,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="config/registry-manager-config.json",
        help="Registry manager config path",
    )
    parser.add_argument(
        "--output",
        default="results/mechanical_ethics_gate.json",
        help="Output gate artifact path",
    )
    parser.add_argument(
        "--sectors",
        default=",".join(DEFAULT_SECTORS),
        help="Comma-separated sectors to evaluate",
    )
    parser.add_argument(
        "--required-sectors",
        default=os.getenv("ETHICBIT_ME_GATE_REQUIRED_SECTORS", "CORE,TECHNICAL"),
        help="Comma-separated required sectors for PASS",
    )
    args = parser.parse_args()

    sectors = parse_csv(args.sectors)
    required_sectors = parse_csv(args.required_sectors)

    manager = RegistryManager(str((ROOT / args.config).resolve()))
    evidence_mode = manager.evidence_broker.mode.upper()

    eval_data = asyncio.run(evaluate_gate(manager, sectors))
    per_sector = eval_data["per_sector"]

    validated_sectors = [s for s, d in per_sector.items() if d["status"] == "PASS"]
    failed_sectors = [s for s, d in per_sector.items() if d["status"] == "FAIL_CLOSED"]
    unsupported_sectors = [s for s, d in per_sector.items() if d["status"] == "UNSUPPORTED"]
    required_failed = [s for s in required_sectors if s not in validated_sectors]

    blocking_reasons: List[str] = []
    if evidence_mode == "MOCK":
        blocking_reasons.append("MOCK_NOT_ALLOWED_IN_CANONICAL_GATE")
    if required_failed:
        blocking_reasons.append("REQUIRED_SECTORS_NOT_VALIDATED")

    status = "PASS" if not blocking_reasons else "FAIL_CLOSED"
    l4_blockers: List[str] = []
    l4_missing_evidence_by_sector: Dict[str, List[str]] = {}
    for sector in L4_FOUNDATIONAL_SECTORS:
        sector_data = per_sector.get(sector, {})
        missing = list(sector_data.get("missing_evidence_keys", []))
        if missing:
            l4_missing_evidence_by_sector[sector] = missing

        if sector_data.get("status") != "PASS":
            l4_blockers.append(f"L4_SECTOR_NOT_VALIDATED:{sector}")

    if evidence_mode != "REAL_LOCAL":
        l4_blockers.append("L4_REQUIRES_REAL_LOCAL_MODE")
    if l4_missing_evidence_by_sector:
        l4_blockers.append("L4_MISSING_FOUNDATIONAL_EVIDENCE")

    claim_level_ceiling = "L4" if status == "PASS" and not l4_blockers else "L3"
    foundational_validated = not l4_missing_evidence_by_sector and all(
        per_sector.get(sector, {}).get("status") == "PASS"
        for sector in L4_FOUNDATIONAL_SECTORS
    )

    payload = {
        "artifactType": "mechanical_ethics_gate",
        "schemaVersion": "1.0.0",
        "generatedAt": utc_now(),
        "status": status,
        "blocking": status != "PASS",
        "mode": evidence_mode,
        "evidence_mode": "REAL_LOCAL",
        "claim_level_ceiling": claim_level_ceiling,
        "l4_foundational_sectors": L4_FOUNDATIONAL_SECTORS,
        "l4_foundational_validated": foundational_validated,
        "l4_blockers": sorted(set(l4_blockers)),
        "l4_missing_evidence_by_sector": l4_missing_evidence_by_sector,
        "required_sectors": required_sectors,
        "validated_sectors": validated_sectors,
        "failed_sectors": failed_sectors,
        "unsupported_sectors": unsupported_sectors,
        "required_failed_sectors": required_failed,
        "blocking_reasons": blocking_reasons,
        "policy": {
            "canonical_audit": True,
            "allow_mock_in_canonical_audit": bool(
                manager.evidence_broker.allow_mock_in_canonical_audit
            ),
            "mock_forbidden_in_gate": True,
        },
        "sectors": per_sector,
        "results": eval_data["per_rule"],
    }

    out_path = (ROOT / args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"mechanical_ethics_gate={out_path}")
    print(f"status={status}")
    print(f"mode={evidence_mode}")
    print(f"required_failed={required_failed}")

    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
