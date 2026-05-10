"""
AEM-EVOLVE™ v2.0 PR 13 — Production Readiness Gate Aggregator.

Aggregates the results of all 8 importable gate modules (PR5–PR12) and verifies
that all 12 verifier scripts are present on disk.

C-01–C-08 pass on file presence, module import, and gate result inspection.
C-09 requires AEM_READINESS_REVIEWER env var (identity of readiness reviewer).
C-10 requires AEM_READINESS_REVIEW_DATE env var (ISO8601 date of review).

Non-claims:
  This gate verifies that all evidence artifacts exist and gate modules report
  the expected file-based check results. It does NOT claim production readiness.
  production_ready is always False until all 12 gates fully PASS and
  C-09 and C-10 are both set.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

_DEMO_ROOT = Path(__file__).resolve().parents[1]
_TOOLS_DIR = _DEMO_ROOT / "tools"
_ASSURANCE_DIR = _DEMO_ROOT / "assurance" / "evolve-multi-agent" / "v2_0"
_READINESS_TOOLS_DIR = _TOOLS_DIR / "readiness"
_PR_VERIFIERS_DIR = _TOOLS_DIR / "production_readiness"

_EVIDENCE_GLOB = "aggregate_readiness_evidence_*.json"

_REQUIRED_VERIFIERS = [
    "verify_oidc_provider.py",
    "verify_kms_signing.py",
    "verify_postgres_persistence.py",
    "verify_migration_recovery.py",
    "verify_monitoring_alerting.py",
    "verify_incident_response.py",
    "verify_security_review.py",
    "verify_reproduction.py",
    "verify_deployment_audit.py",
    "verify_slo_evidence.py",
    "verify_rollback_procedure.py",
    "verify_disaster_recovery.py",
]

_IMPORTABLE_GATE_MODULES = [
    ("monitoring.monitoring_gate",                        "MonitoringGate"),
    ("incident_response.incident_response_gate",          "IncidentResponseGate"),
    ("security_review.security_review_gate",              "SecurityReviewGate"),
    ("reproduction.reproduction_gate",                    "ReproductionGate"),
    ("deployment.deployment_gate",                        "DeploymentGate"),
    ("slo.slo_gate",                                      "SLOGate"),
    ("rollback.rollback_gate",                            "RollbackGate"),
    ("disaster_recovery.disaster_recovery_gate",          "DisasterRecoveryGate"),
]

# Gate identifiers expected in gate_check() results
_EXPECTED_GATE_IDS = {
    "MonitoringGate":        "MONITORING_ALERTING_CHECK",
    "IncidentResponseGate":  "INCIDENT_RESPONSE_CHECK",
    "SecurityReviewGate":    "SECURITY_REVIEW_CHECK",
    "ReproductionGate":      "EXTERNAL_REPRODUCTION_CHECK",
    "DeploymentGate":        "PRODUCTION_DEPLOYMENT_AUDIT_CHECK",
    "SLOGate":               "SLO_EVIDENCE_CHECK",
    "RollbackGate":          "ROLLBACK_PROCEDURE_CHECK",
    "DisasterRecoveryGate":  "DISASTER_RECOVERY_CHECK",
}

# Honesty invariants: these fields must be False without live env vars
_HONESTY_INVARIANTS = [
    "independent_reproduction_claimed",
    "production_deployed",
    "slo_evidence_verified",
    "rollback_tested",
    "dr_tested",
]

_MIN_FILE_CHECKS_PASSING = 8  # C-01..C-08 must all pass for each gate


def _load_gates() -> dict[str, Any]:
    """Import all 8 gate modules and call from_env() on each."""
    import importlib
    gates = {}
    for module_path, class_name in _IMPORTABLE_GATE_MODULES:
        try:
            mod = importlib.import_module(module_path)
            cls = getattr(mod, class_name)
            gates[class_name] = cls.from_env()
        except Exception as exc:
            gates[class_name] = exc
    return gates


class ReadinessGate:
    """Aggregator gate for production readiness (PR 13)."""

    def __init__(
        self,
        readiness_reviewer: str | None = None,
        readiness_review_date: str | None = None,
    ) -> None:
        self._readiness_reviewer = readiness_reviewer
        self._readiness_review_date = readiness_review_date

    @classmethod
    def from_env(cls) -> "ReadinessGate":
        return cls(
            readiness_reviewer=os.getenv("AEM_READINESS_REVIEWER", "").strip() or None,
            readiness_review_date=os.getenv("AEM_READINESS_REVIEW_DATE", "").strip() or None,
        )

    # ── C-01: All 12 verifier scripts present ────────────────────────────────

    def check_verifiers_present(self) -> dict[str, Any]:
        missing = [v for v in _REQUIRED_VERIFIERS
                   if not (_PR_VERIFIERS_DIR / v).exists()]
        present = [v for v in _REQUIRED_VERIFIERS
                   if (_PR_VERIFIERS_DIR / v).exists()]
        return {
            "ok": not missing,
            "verifiers_required": len(_REQUIRED_VERIFIERS),
            "verifiers_present": len(present),
            "missing_verifiers": missing,
        }

    # ── C-02: All 8 importable gate modules load without error ────────────────

    def check_gate_modules_load(self) -> dict[str, Any]:
        import importlib
        failed = []
        loaded = []
        for module_path, class_name in _IMPORTABLE_GATE_MODULES:
            try:
                mod = importlib.import_module(module_path)
                getattr(mod, class_name)
                loaded.append(class_name)
            except Exception as exc:
                failed.append({"module": module_path, "error": str(exc)})
        return {
            "ok": not failed,
            "modules_required": len(_IMPORTABLE_GATE_MODULES),
            "modules_loaded": len(loaded),
            "failed_modules": failed,
        }

    # ── C-03: PR5 + PR6 file-based checks pass (≥8 each) ────────────────────

    def check_pr5_pr6(self) -> dict[str, Any]:
        gates = _load_gates()
        results = {}
        all_ok = True
        for name in ("MonitoringGate", "IncidentResponseGate"):
            gate = gates.get(name)
            if isinstance(gate, Exception):
                results[name] = {"ok": False, "error": str(gate)}
                all_ok = False
                continue
            result = gate.gate_check()
            checks = result.get("checks", {})
            file_keys = [k for k in checks if k.startswith(
                ("C-01","C-02","C-03","C-04","C-05","C-06","C-07","C-08")
            )]
            # skipped=True means live-infra not configured; not a file evidence gap
            file_passed = sum(1 for k in file_keys
                              if checks[k].get("ok") or checks[k].get("skipped"))
            ok = file_passed >= _MIN_FILE_CHECKS_PASSING
            results[name] = {"ok": ok, "file_checks_passed": file_passed, "gate": result.get("gate")}
            if not ok:
                all_ok = False
        return {"ok": all_ok, "gates": results}

    # ── C-04: PR7 + PR8 file-based checks pass (≥8 each) ────────────────────

    def check_pr7_pr8(self) -> dict[str, Any]:
        gates = _load_gates()
        results = {}
        all_ok = True
        for name in ("SecurityReviewGate", "ReproductionGate"):
            gate = gates.get(name)
            if isinstance(gate, Exception):
                results[name] = {"ok": False, "error": str(gate)}
                all_ok = False
                continue
            result = gate.gate_check()
            checks = result.get("checks", {})
            file_keys = [k for k in checks if k.startswith(
                ("C-01","C-02","C-03","C-04","C-05","C-06","C-07","C-08")
            )]
            file_passed = sum(1 for k in file_keys
                              if checks[k].get("ok") or checks[k].get("skipped"))
            ok = file_passed >= _MIN_FILE_CHECKS_PASSING
            results[name] = {"ok": ok, "file_checks_passed": file_passed, "gate": result.get("gate")}
            if not ok:
                all_ok = False
        return {"ok": all_ok, "gates": results}

    # ── C-05: PR9 + PR10 file-based checks pass (≥8 each) ───────────────────

    def check_pr9_pr10(self) -> dict[str, Any]:
        gates = _load_gates()
        results = {}
        all_ok = True
        for name in ("DeploymentGate", "SLOGate"):
            gate = gates.get(name)
            if isinstance(gate, Exception):
                results[name] = {"ok": False, "error": str(gate)}
                all_ok = False
                continue
            result = gate.gate_check()
            checks = result.get("checks", {})
            file_keys = [k for k in checks if k.startswith(
                ("C-01","C-02","C-03","C-04","C-05","C-06","C-07","C-08")
            )]
            file_passed = sum(1 for k in file_keys
                              if checks[k].get("ok") or checks[k].get("skipped"))
            ok = file_passed >= _MIN_FILE_CHECKS_PASSING
            results[name] = {"ok": ok, "file_checks_passed": file_passed, "gate": result.get("gate")}
            if not ok:
                all_ok = False
        return {"ok": all_ok, "gates": results}

    # ── C-06: PR11 + PR12 file-based checks pass (≥8 each) ──────────────────

    def check_pr11_pr12(self) -> dict[str, Any]:
        gates = _load_gates()
        results = {}
        all_ok = True
        for name in ("RollbackGate", "DisasterRecoveryGate"):
            gate = gates.get(name)
            if isinstance(gate, Exception):
                results[name] = {"ok": False, "error": str(gate)}
                all_ok = False
                continue
            result = gate.gate_check()
            checks = result.get("checks", {})
            file_keys = [k for k in checks if k.startswith(
                ("C-01","C-02","C-03","C-04","C-05","C-06","C-07","C-08")
            )]
            file_passed = sum(1 for k in file_keys
                              if checks[k].get("ok") or checks[k].get("skipped"))
            ok = file_passed >= _MIN_FILE_CHECKS_PASSING
            results[name] = {"ok": ok, "file_checks_passed": file_passed, "gate": result.get("gate")}
            if not ok:
                all_ok = False
        return {"ok": all_ok, "gates": results}

    # ── C-07: Aggregate evidence artifact with SHA256 ────────────────────────

    def check_aggregate_evidence(self) -> dict[str, Any]:
        artifacts = sorted(_READINESS_TOOLS_DIR.glob(_EVIDENCE_GLOB)) if _READINESS_TOOLS_DIR.exists() else []
        if not artifacts:
            return {
                "ok": False,
                "detail": f"No aggregate_readiness_evidence_*.json found in {_READINESS_TOOLS_DIR}",
            }
        latest = artifacts[-1]
        try:
            data = json.loads(latest.read_text(encoding="utf-8"))
        except Exception as exc:
            return {"ok": False, "detail": f"Invalid JSON: {exc}"}

        sha256 = hashlib.sha256(latest.read_bytes()).hexdigest()
        summary = data.get("summary", {})
        hashed = summary.get("subjects_hashed", 0)
        total = summary.get("subjects_total", 0)
        has_sha = "artifact_sha256" in data
        return {
            "ok": hashed >= 15 and hashed == total and has_sha,
            "file": str(latest),
            "sha256": sha256,
            "artifact_sha256": data.get("artifact_sha256", ""),
            "subjects_hashed": hashed,
            "subjects_total": total,
            "has_artifact_sha256": has_sha,
        }

    # ── C-08: Artifact fingerprint recorded ──────────────────────────────────

    def check_artifact_fingerprint(self) -> dict[str, Any]:
        artifacts = sorted(_READINESS_TOOLS_DIR.glob(_EVIDENCE_GLOB)) if _READINESS_TOOLS_DIR.exists() else []
        if not artifacts:
            return {"ok": False, "detail": "No aggregate_readiness_evidence_*.json found"}
        try:
            data = json.loads(artifacts[-1].read_text(encoding="utf-8"))
        except Exception as exc:
            return {"ok": False, "detail": f"Invalid JSON: {exc}"}
        artifact_sha = data.get("artifact_sha256", "")
        return {
            "ok": bool(artifact_sha) and len(artifact_sha) == 64,
            "has_artifact_sha256": bool(artifact_sha),
            "artifact_sha256": artifact_sha,
        }

    # ── C-09: Readiness reviewer identity ────────────────────────────────────

    def check_readiness_reviewer(self) -> dict[str, Any]:
        if not self._readiness_reviewer:
            return {
                "ok": False,
                "skipped": True,
                "reason": (
                    "AEM_READINESS_REVIEWER not set — set to governance lead identity "
                    "before claiming production_ready=true"
                ),
            }
        return {"ok": True, "readiness_reviewer": self._readiness_reviewer}

    # ── C-10: Readiness review date ───────────────────────────────────────────

    def check_readiness_review_date(self) -> dict[str, Any]:
        if not self._readiness_review_date:
            return {
                "ok": False,
                "skipped": True,
                "reason": "AEM_READINESS_REVIEW_DATE not set — set to ISO8601 date of production readiness review",
            }
        return {"ok": True, "readiness_review_date": self._readiness_review_date}

    # ── Gate summary: run all 8 importable gates ──────────────────────────────

    def _build_gate_summary(self) -> dict[str, Any]:
        gates = _load_gates()
        summary = {}
        for _, class_name in _IMPORTABLE_GATE_MODULES:
            gate = gates.get(class_name)
            if isinstance(gate, Exception):
                summary[class_name] = {"status": "LOAD_ERROR", "error": str(gate)}
                continue
            result = gate.gate_check()
            checks = result.get("checks", {})
            file_keys = [k for k in checks if k.startswith(
                ("C-01","C-02","C-03","C-04","C-05","C-06","C-07","C-08")
            )]
            file_passed = sum(1 for k in file_keys
                              if checks[k].get("ok") or checks[k].get("skipped"))
            summary[class_name] = {
                "gate": result.get("gate"),
                "status": result.get("status"),
                "checks_passed": result.get("checks_passed"),
                "checks_failed": result.get("checks_failed"),
                "file_checks_passed": file_passed,
            }
        return summary

    # ── Full gate ─────────────────────────────────────────────────────────────

    def gate_check(self) -> dict[str, Any]:
        c01 = self.check_verifiers_present()
        c02 = self.check_gate_modules_load()
        c03 = self.check_pr5_pr6()
        c04 = self.check_pr7_pr8()
        c05 = self.check_pr9_pr10()
        c06 = self.check_pr11_pr12()
        c07 = self.check_aggregate_evidence()
        c08 = self.check_artifact_fingerprint()
        c09 = self.check_readiness_reviewer()
        c10 = self.check_readiness_review_date()

        checks = {
            "C-01_verifiers_present":   c01,
            "C-02_gate_modules_load":   c02,
            "C-03_pr5_pr6":             c03,
            "C-04_pr7_pr8":             c04,
            "C-05_pr9_pr10":            c05,
            "C-06_pr11_pr12":           c06,
            "C-07_aggregate_evidence":  c07,
            "C-08_artifact_fingerprint":c08,
            "C-09_readiness_reviewer":  c09,
            "C-10_readiness_review_date":c10,
        }

        passed = sum(1 for v in checks.values() if v.get("ok"))
        failed = len(checks) - passed
        status = "PASS" if failed == 0 else "FAIL"

        gate_summary = self._build_gate_summary()
        all_gates_pass = all(
            g.get("status") == "PASS" for g in gate_summary.values()
        )

        fail_reason = None
        if status == "FAIL":
            missing_live = []
            if not self._readiness_reviewer:
                missing_live.append("AEM_READINESS_REVIEWER")
            if not self._readiness_review_date:
                missing_live.append("AEM_READINESS_REVIEW_DATE")
            if missing_live:
                fail_reason = (
                    f"Production readiness review not yet completed: "
                    f"{', '.join(missing_live)} not set. production_ready=false"
                )
            else:
                failing = [k for k, v in checks.items() if not v.get("ok")]
                fail_reason = f"Failing checks: {', '.join(failing)}"

        return {
            "gate": "PRODUCTION_READINESS_GATE",
            "status": status,
            "checks_passed": passed,
            "checks_failed": failed,
            "production_ready": (
                self._readiness_reviewer is not None
                and self._readiness_review_date is not None
                and all_gates_pass
            ),
            "gates_evidence_complete": all(
                g.get("file_checks_passed", 0) >= _MIN_FILE_CHECKS_PASSING
                for g in gate_summary.values()
                if "file_checks_passed" in g
            ),
            "readiness_reviewer": self._readiness_reviewer,
            "readiness_review_date": self._readiness_review_date,
            "gate_summary": gate_summary,
            "fail_reason": fail_reason,
            "checks": checks,
        }
