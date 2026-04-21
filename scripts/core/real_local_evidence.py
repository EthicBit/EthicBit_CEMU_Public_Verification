#!/usr/bin/env python3
"""REAL_LOCAL evidence resolver for Mechanical Ethics gates."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


EVIDENCE_PATH_MAP: Dict[str, List[str]] = {
    # CORE
    "audit_log": [
        "artifacts/cases/case_003/runtime_audit_trail.case_003.canonical.json",
        "results/GATE_REPORT.json",
    ],
    "decision_chain": [
        "artifacts/cases/case_003/closure_state.case_003.canonical.json",
    ],
    "timestamped_snapshot": [
        "artifacts/history/swarm/official_operational_status.json",
        "artifacts/cases/case_003/closure_state.case_003.canonical.json",
    ],
    "immutable_storage": [
        "artifacts/cases/case_003/verification_pack.case_003.canonical.json",
    ],
    "blockchain_anchor": [
        "artifacts/cases/case_003/anchor_receipt.case_003.canonical.json",
    ],
    "cryptographic_hash": [
        "artifacts/ethicbit_closure_artifacts_hashes.json",
    ],
    "explanation_log": [
        "results/technical_verification.md",
        "results/legal_claim_boundary.md",
    ],
    "causal_graph": [
        "artifacts/cases/case_003/closure_state.case_003.canonical.json",
    ],
    "model_trace": [
        "artifacts/cases/case_003/runtime_audit_trail.case_003.canonical.json",
    ],
    # JUSTICIA
    "judicial_reasoning_log": [
        "results/legal_claim_boundary.md",
    ],
    "evidence_chain": [
        "artifacts/cases/case_003/case_bundle.case_003.canonical.json",
        "artifacts/cases/case_003/verification_pack.case_003.canonical.json",
    ],
    "replay_proof": [
        "artifacts/cases/case_003/runtime_audit_trail.case_003.canonical.json",
    ],
    "input_snapshot": [
        "artifacts/cases/case_003/canonical_root.case_003.json",
    ],
    "appeal_deadline_log": [
        "results/legal_claim_boundary.md",
    ],
    "notification_record": [
        "results/public_summary.md",
    ],
    # FINANZAS
    "transaction_ledger": [
        "artifacts/ethicbit_closure_artifacts_hashes.json",
    ],
    "source_funds_proof": [
        "artifacts/security_incident_bundle_v1_0.json",
    ],
    "audit_trail": [
        "artifacts/cases/case_003/runtime_audit_trail.case_003.canonical.json",
    ],
    "fee_schedule": [
        "results/finance_anchor_report.md",
    ],
    "cost_disclosure_log": [
        "results/finance_anchor_report.md",
    ],
    "contract_review": [
        "contracts/ClosureAnchor.sol",
    ],
    "model_version": [
        "package-lock.json",
    ],
    # SECURITY
    "security_event_log": [
        "artifacts/cases/case_003/runtime_audit_trail.case_003.canonical.json",
    ],
    "identity_binding_log": [
        "artifacts/cases/case_003/human_approval.case_003.canonical.json",
    ],
    "privileged_action_trace": [
        "artifacts/cases/case_003/runtime_audit_trail.case_003.canonical.json",
    ],
    "execution_context_record": [
        "artifacts/cases/case_003/runtime_audit_trail.case_003.canonical.json",
    ],
    "verification_input_snapshot": [
        "artifacts/cases/case_003/verification_environment.case_003.canonical.json",
    ],
    "config_snapshot": [
        "config/registry-manager-config.json",
    ],
    # TECHNICAL
    "source_snapshot": [
        "artifacts/cases/case_003/canonical_root.case_003.json",
    ],
    "build_config": [
        "hardhat.config.js",
        "foundry.toml",
    ],
    "dependency_lock": [
        "package-lock.json",
    ],
    "transformation_log": [
        "artifacts/cases/case_003/runtime_audit_trail.case_003.canonical.json",
    ],
    "intermediate_state_record": [
        "artifacts/cases/case_003/closure_state.case_003.canonical.json",
    ],
    "output_manifest": [
        "artifacts/cases/case_003/artifact_manifest.case_003.canonical.json",
    ],
    "verification_report": [
        "results/technical_verification.md",
    ],
    "failure_reason_log": [
        "results/GATE_REPORT.json",
    ],
    "remediation_record": [
        "results/legal_claim_boundary.md",
    ],
    "runtime_signal_trace": [
        "artifacts/cases/case_003/runtime_audit_trail.case_003.canonical.json",
    ],
    "event_correlation_record": [
        "artifacts/cases/case_003/runtime_audit_trail.case_003.canonical.json",
    ],
    "technical_detection_snapshot": [
        "artifacts/cases/case_003/runtime_constitutional_assessment.case_003.canonical.json",
    ],
    "agent_interaction_log": [
        "artifacts/cases/case_003/runtime_audit_trail.case_003.canonical.json",
    ],
    "orchestration_trace": [
        "artifacts/cases/case_003/runtime_audit_trail.case_003.canonical.json",
    ],
    "reproducibility_control_record": [
        "artifacts/cases/case_003/verification_pack.case_003.canonical.json",
    ],
    "detectability_assessment": [
        "artifacts/cases/case_003/runtime_constitutional_assessment.case_003.canonical.json",
    ],
    "impact_trace_record": [
        "artifacts/cases/case_003/runtime_constitutional_assessment.case_003.canonical.json",
    ],
    "control_decision_log": [
        "artifacts/cases/case_003/runtime_audit_trail.case_003.canonical.json",
        "results/constitutional_controls_report.json",
    ],
    "impact_scope_matrix": [
        "results/constitutional_amendment_snapshot.json",
    ],
    "cross_sector_trigger_record": [
        "results/constitutional_controls_report.json",
    ],
    "supervisory_trace_record": [
        "results/regulatory_control_report.md",
    ],
    # LEGAL
    "evidence_chain_log": [
        "artifacts/cases/case_003/case_bundle.case_003.canonical.json",
    ],
    "source_reference_record": [
        "results/legal_claim_boundary.md",
    ],
    "policy_snapshot": [
        "config/registry-manager-config.json",
    ],
    "decision_explanation": [
        "results/legal_claim_boundary.md",
    ],
    "causal_chain_record": [
        "artifacts/cases/case_003/closure_state.case_003.canonical.json",
    ],
    "compliance_replay_script": [
        "scripts/run_mixed_audience_audit.sh",
    ],
    "reasoning_log": [
        "results/legal_claim_boundary.md",
    ],
    # REGULATORY
    "regulatory_trace_record": [
        "results/regulatory_control_report.md",
    ],
    "supervisory_summary": [
        "results/regulatory_control_report.md",
    ],
    "finding_explanation_record": [
        "results/regulatory_control_report.md",
        "results/technical_verification.md",
    ],
    "reproduction_script": [
        "scripts/run_mixed_audience_audit.sh",
        "scripts/audit/final_closure_audit.sh",
    ],
    # External/broker keys (forward compatibility)
    "price": [
        "results/finance_anchor_report.md",
    ],
    "identity": [
        "artifacts/cases/case_003/human_approval.case_003.canonical.json",
    ],
    "kycVerification": [
        "artifacts/cases/case_003/human_approval.case_003.canonical.json",
    ],
    "financialTxHash": [
        "artifacts/security_incident_bundle_v1_0.json",
    ],
    "cryptographicSignature": [
        "artifacts/history/swarm/official_operational_status.json",
    ],
}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _utc_iso_from_timestamp(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _first_existing_path(paths: Iterable[str], root_dir: Path) -> Path | None:
    for rel in paths:
        candidate = root_dir / rel
        if candidate.exists():
            return candidate
    return None


def _file_evidence_record(path: Path, root_dir: Path, evidence_key: str) -> Dict[str, Any]:
    stat = path.stat()
    return {
        "evidence_key": evidence_key,
        "path": str(path.relative_to(root_dir)),
        "sha256": _sha256_file(path),
        "size_bytes": stat.st_size,
        "modified_at": _utc_iso_from_timestamp(stat.st_mtime),
        "source_type": "REAL_LOCAL_FILE",
    }


def _resolve_human_approval(path: Path, root_dir: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    approval_status = str(data.get("approval_status", "")).upper()
    approved = approval_status == "APPROVED"
    approver = data.get("approver_id") or data.get("approver_role") or "unknown"
    timestamp = data.get("approval_timestamp") or ""
    signature_basis = _sha256_file(path)
    return {
        "approved": approved,
        "approver": approver,
        "timestamp": timestamp,
        "signature": f"attest::real-local-human-approval::{signature_basis}",
        "record": _file_evidence_record(path, root_dir, "humanApproval"),
    }


def resolve_required_evidence(
    required_keys: Iterable[str],
    root_dir: Path | None = None,
) -> Tuple[Dict[str, Any], List[str], Dict[str, Any]]:
    root = (root_dir or Path(".")).resolve()
    evidence: Dict[str, Any] = {}
    missing: List[str] = []
    trace: Dict[str, Any] = {
        "mode": "REAL_LOCAL",
        "resolved": {},
        "missing": [],
    }

    for key in required_keys:
        candidates = EVIDENCE_PATH_MAP.get(key, [])
        selected = _first_existing_path(candidates, root)
        if selected is None:
            missing.append(key)
            trace["missing"].append(
                {
                    "evidence_key": key,
                    "candidate_paths": candidates,
                    "reason": "NO_REAL_LOCAL_SOURCE_FOUND",
                }
            )
            continue

        if key == "humanApproval":
            value = _resolve_human_approval(selected, root)
        else:
            value = _file_evidence_record(selected, root, key)

        evidence[key] = value
        trace["resolved"][key] = value.get("path", str(selected.relative_to(root)))

    return evidence, missing, trace
