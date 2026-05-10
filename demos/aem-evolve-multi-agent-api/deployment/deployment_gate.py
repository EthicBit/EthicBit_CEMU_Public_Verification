"""
AEM-EVOLVE™ v2.0 PR 9 — Production Deployment Audit Evidence Gate.

C-01–C-08 pass on file presence and content inspection (no live infra needed).
C-09 requires AEM_DEPLOYMENT_TARGET env var (production deployment identifier).
C-10 requires AEM_DEPLOYMENT_TIMESTAMP env var (ISO8601 deployment timestamp).

Non-claims:
  This gate verifies that deployment audit artifacts exist and are structurally
  complete. It does NOT claim a production deployment has occurred.
  production_deployed is always False until C-09 and C-10 are both set.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

_DEMO_ROOT = Path(__file__).resolve().parents[1]
_DOCS_DIR = _DEMO_ROOT / "docs"
_DEPLOY_TOOLS_DIR = _DEMO_ROOT / "tools" / "deployment"
_PR_VERIFIERS_DIR = _DEMO_ROOT / "tools" / "production_readiness"

_MANIFEST_FILE = _DOCS_DIR / "DEPLOYMENT_MANIFEST.md"
_AUDIT_GLOB = "deployment_audit_*.json"

_REQUIRED_ENV_VARS = [
    "OIDC_ISSUER",
    "AEM_KMS_PROVIDER",
    "AEM_KMS_KEY_ID",
    "AEM_DB_URL",
    "AEM_DB_ADAPTER",
    "AEM_PROMETHEUS_URL",
    "AEM_DRILL_COMPLETED_AT",
    "AEM_DRILL_SIGNOFF_APPROVER",
    "AEM_SECURITY_REVIEWER",
    "AEM_SECURITY_REVIEW_DATE",
    "AEM_REPRODUCER_ID",
    "AEM_REPRODUCTION_DATE",
    "HITL_SECRET",
    "AEM_DEMO_AUTH_KEYS_JSON",
]

_REQUIRED_GATES = [
    "PR1", "PR2", "PR3", "PR4", "PR5", "PR6", "PR7", "PR8", "PR9",
]

_REQUIRED_GATE_VERIFIERS = [
    "verify_oidc_provider.py",
    "verify_kms_signing.py",
    "verify_postgres_persistence.py",
    "verify_migration_recovery.py",
    "verify_monitoring_alerting.py",
    "verify_incident_response.py",
    "verify_security_review.py",
    "verify_reproduction.py",
    "verify_deployment_audit.py",
]

_HEALTH_ENDPOINTS = ["/health", "/healthz", "/metrics"]


class DeploymentGate:
    """Gate verifier for production deployment audit evidence (PR 9)."""

    def __init__(
        self,
        deployment_target: str | None = None,
        deployment_timestamp: str | None = None,
    ) -> None:
        self._deployment_target = deployment_target
        self._deployment_timestamp = deployment_timestamp

    @classmethod
    def from_env(cls) -> "DeploymentGate":
        return cls(
            deployment_target=os.getenv("AEM_DEPLOYMENT_TARGET", "").strip() or None,
            deployment_timestamp=os.getenv("AEM_DEPLOYMENT_TIMESTAMP", "").strip() or None,
        )

    # ── C-01: Deployment manifest exists ─────────────────────────────────────

    def check_manifest(self) -> dict[str, Any]:
        if not _MANIFEST_FILE.exists():
            return {"ok": False, "detail": f"DEPLOYMENT_MANIFEST.md not found at {_MANIFEST_FILE}"}
        content = _MANIFEST_FILE.read_text(encoding="utf-8")
        sha256 = hashlib.sha256(content.encode()).hexdigest()
        return {
            "ok": True,
            "file": str(_MANIFEST_FILE),
            "sha256": sha256,
            "size_bytes": len(content.encode()),
        }

    # ── C-02: Manifest specifies target environment fields ────────────────────

    def check_target_environment(self) -> dict[str, Any]:
        if not _MANIFEST_FILE.exists():
            return {"ok": False, "detail": "DEPLOYMENT_MANIFEST.md missing"}
        content = _MANIFEST_FILE.read_text(encoding="utf-8")
        required_fields = [
            "environment_name", "cloud_provider", "region",
            "deployment_date", "version_tag", "container_image_digest",
        ]
        missing = [f for f in required_fields if f not in content]
        return {
            "ok": not missing,
            "fields_required": len(required_fields),
            "fields_present": len(required_fields) - len(missing),
            "missing_fields": missing,
        }

    # ── C-03: Required env vars documented ───────────────────────────────────

    def check_env_vars_documented(self) -> dict[str, Any]:
        if not _MANIFEST_FILE.exists():
            return {"ok": False, "detail": "DEPLOYMENT_MANIFEST.md missing"}
        content = _MANIFEST_FILE.read_text(encoding="utf-8")
        missing = [v for v in _REQUIRED_ENV_VARS if v not in content]
        return {
            "ok": not missing,
            "env_vars_required": len(_REQUIRED_ENV_VARS),
            "env_vars_documented": len(_REQUIRED_ENV_VARS) - len(missing),
            "missing_env_vars": missing,
        }

    # ── C-04: Pre-deployment checklist covers all 9 gates ────────────────────

    def check_gate_checklist(self) -> dict[str, Any]:
        if not _MANIFEST_FILE.exists():
            return {"ok": False, "detail": "DEPLOYMENT_MANIFEST.md missing"}
        content = _MANIFEST_FILE.read_text(encoding="utf-8")
        missing = [g for g in _REQUIRED_GATES if g not in content]
        return {
            "ok": not missing,
            "gates_required": len(_REQUIRED_GATES),
            "gates_in_checklist": len(_REQUIRED_GATES) - len(missing),
            "missing_gates": missing,
        }

    # ── C-05: All 9 gate verifier scripts exist ───────────────────────────────

    def check_gate_verifiers(self) -> dict[str, Any]:
        if not _PR_VERIFIERS_DIR.exists():
            return {"ok": False, "detail": f"Verifiers dir not found: {_PR_VERIFIERS_DIR}"}
        missing = [v for v in _REQUIRED_GATE_VERIFIERS
                   if not (_PR_VERIFIERS_DIR / v).exists()]
        present = [v for v in _REQUIRED_GATE_VERIFIERS
                   if (_PR_VERIFIERS_DIR / v).exists()]
        return {
            "ok": not missing,
            "verifiers_required": len(_REQUIRED_GATE_VERIFIERS),
            "verifiers_present": len(present),
            "missing_verifiers": missing,
        }

    # ── C-06: Rollback plan documented ───────────────────────────────────────

    def check_rollback_plan(self) -> dict[str, Any]:
        if not _MANIFEST_FILE.exists():
            return {"ok": False, "detail": "DEPLOYMENT_MANIFEST.md missing"}
        content = _MANIFEST_FILE.read_text(encoding="utf-8")
        has_rollback = "Rollback Plan" in content or "rollback" in content.lower()
        has_steps = "Roll back" in content or "rollback" in content.lower()
        has_db_rollback = "rollback" in content.lower() and "migrations/rollback" in content
        return {
            "ok": has_rollback and has_steps and has_db_rollback,
            "has_rollback_section": has_rollback,
            "has_rollback_steps": has_steps,
            "has_db_rollback_reference": has_db_rollback,
        }

    # ── C-07: Health check endpoints documented ───────────────────────────────

    def check_health_endpoints(self) -> dict[str, Any]:
        if not _MANIFEST_FILE.exists():
            return {"ok": False, "detail": "DEPLOYMENT_MANIFEST.md missing"}
        content = _MANIFEST_FILE.read_text(encoding="utf-8")
        missing = [ep for ep in _HEALTH_ENDPOINTS if ep not in content]
        return {
            "ok": not missing,
            "endpoints_required": len(_HEALTH_ENDPOINTS),
            "endpoints_documented": len(_HEALTH_ENDPOINTS) - len(missing),
            "missing_endpoints": missing,
        }

    # ── C-08: Deployment audit artifact with SHA256 exists ───────────────────

    def check_audit_artifact(self) -> dict[str, Any]:
        artifacts = sorted(_DEPLOY_TOOLS_DIR.glob(_AUDIT_GLOB)) if _DEPLOY_TOOLS_DIR.exists() else []
        if not artifacts:
            return {
                "ok": False,
                "detail": (
                    f"No deployment_audit_*.json found in {_DEPLOY_TOOLS_DIR}. "
                    "Run: python tools/production_readiness/verify_deployment_audit.py --generate"
                ),
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

    # ── C-09: Deployment target set ──────────────────────────────────────────

    def check_deployment_target(self) -> dict[str, Any]:
        if not self._deployment_target:
            return {
                "ok": False,
                "skipped": True,
                "reason": (
                    "AEM_DEPLOYMENT_TARGET not set — set to production deployment identifier "
                    "(e.g. 'aws-us-east-1-prod') before claiming production deployment"
                ),
            }
        return {"ok": True, "deployment_target": self._deployment_target}

    # ── C-10: Deployment timestamp set ───────────────────────────────────────

    def check_deployment_timestamp(self) -> dict[str, Any]:
        if not self._deployment_timestamp:
            return {
                "ok": False,
                "skipped": True,
                "reason": "AEM_DEPLOYMENT_TIMESTAMP not set — set to ISO8601 timestamp of production deployment",
            }
        return {"ok": True, "deployment_timestamp": self._deployment_timestamp}

    # ── Full gate ─────────────────────────────────────────────────────────────

    def gate_check(self) -> dict[str, Any]:
        c01 = self.check_manifest()
        c02 = self.check_target_environment()
        c03 = self.check_env_vars_documented()
        c04 = self.check_gate_checklist()
        c05 = self.check_gate_verifiers()
        c06 = self.check_rollback_plan()
        c07 = self.check_health_endpoints()
        c08 = self.check_audit_artifact()
        c09 = self.check_deployment_target()
        c10 = self.check_deployment_timestamp()

        checks = {
            "C-01_manifest": c01,
            "C-02_target_environment": c02,
            "C-03_env_vars_documented": c03,
            "C-04_gate_checklist": c04,
            "C-05_gate_verifiers": c05,
            "C-06_rollback_plan": c06,
            "C-07_health_endpoints": c07,
            "C-08_audit_artifact": c08,
            "C-09_deployment_target": c09,
            "C-10_deployment_timestamp": c10,
        }

        passed = sum(1 for v in checks.values() if v.get("ok"))
        failed = len(checks) - passed
        status = "PASS" if failed == 0 else "FAIL"

        fail_reason = None
        if status == "FAIL":
            missing_live = []
            if not self._deployment_target:
                missing_live.append("AEM_DEPLOYMENT_TARGET")
            if not self._deployment_timestamp:
                missing_live.append("AEM_DEPLOYMENT_TIMESTAMP")
            if missing_live:
                fail_reason = (
                    f"Production deployment not yet executed: "
                    f"{', '.join(missing_live)} not set. production_deployed=false"
                )
            else:
                failing = [k for k, v in checks.items() if not v.get("ok")]
                fail_reason = f"Failing checks: {', '.join(failing)}"

        return {
            "gate": "PRODUCTION_DEPLOYMENT_AUDIT_CHECK",
            "status": status,
            "checks_passed": passed,
            "checks_failed": failed,
            "production_deployed": (
                self._deployment_target is not None
                and self._deployment_timestamp is not None
            ),
            "deployment_target": self._deployment_target,
            "deployment_timestamp": self._deployment_timestamp,
            "fail_reason": fail_reason,
            "checks": checks,
        }
