"""
AEM-EVOLVE™ v2.0 PR 8 — External Reproduction Report Evidence Gate.

C-01–C-08 pass on file presence, content, and real checksums (no live infra).
C-09 requires AEM_REPRODUCER_ID env var (external reproducer identity).
C-10 requires AEM_REPRODUCTION_DATE env var (ISO8601 date of external reproduction).

Non-claims:
  This gate verifies that reproduction evidence artifacts exist and are
  structurally complete. It does NOT claim that an external party has
  independently executed and verified the reproduction steps.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

_DEMO_ROOT = Path(__file__).resolve().parents[1]
_DOCS_DIR = _DEMO_ROOT / "docs"
_REPRO_TOOLS_DIR = _DEMO_ROOT / "tools" / "reproduction"

_REPRO_REPORT_V2 = _DOCS_DIR / "REPRODUCTION_REPORT_V2.md"
_REPRO_CHALLENGE = _DOCS_DIR / "REPRODUCTION_CHALLENGE.md"
_EVIDENCE_GLOB = "reproduction_evidence_v2_*.json"
_LEGACY_REPORT = (
    _DEMO_ROOT.parent.parent
    / "assurance" / "evolve-multi-agent"
    / "AEM_EVOLVE_MULTI_AGENT_API_REPRODUCTION_REPORT.json"
)

_REQUIRED_PR_COVERAGE = ["PR1", "PR2", "PR3", "PR4", "PR5", "PR6", "PR7"]
_REQUIRED_OUTCOMES = ["PASS", "SCOPE_LIMITED", "FAIL_CLOSED"]
_REQUIRED_HITL_TERMS = ["HITL", "hitl_token", "replay"]
_REQUIRED_CHAIN_TERMS = ["audit chain", "chain/verify", "tamper"]


class ReproductionGate:
    """Gate verifier for external reproduction report evidence (PR 8)."""

    def __init__(
        self,
        reproducer_id: str | None = None,
        reproduction_date: str | None = None,
    ) -> None:
        self._reproducer_id = reproducer_id
        self._reproduction_date = reproduction_date

    @classmethod
    def from_env(cls) -> "ReproductionGate":
        return cls(
            reproducer_id=os.getenv("AEM_REPRODUCER_ID", "").strip() or None,
            reproduction_date=os.getenv("AEM_REPRODUCTION_DATE", "").strip() or None,
        )

    # ── C-01: v2.0 reproduction report exists ────────────────────────────────

    def check_report_v2(self) -> dict[str, Any]:
        if not _REPRO_REPORT_V2.exists():
            return {"ok": False, "detail": f"REPRODUCTION_REPORT_V2.md not found at {_REPRO_REPORT_V2}"}
        content = _REPRO_REPORT_V2.read_text(encoding="utf-8")
        sha256 = hashlib.sha256(content.encode()).hexdigest()
        return {
            "ok": True,
            "file": str(_REPRO_REPORT_V2),
            "sha256": sha256,
            "size_bytes": len(content.encode()),
        }

    # ── C-02: Reproduction challenge document referenced ──────────────────────

    def check_challenge_doc(self) -> dict[str, Any]:
        if not _REPRO_CHALLENGE.exists():
            return {"ok": False, "detail": f"REPRODUCTION_CHALLENGE.md not found at {_REPRO_CHALLENGE}"}
        sha256 = hashlib.sha256(_REPRO_CHALLENGE.read_bytes()).hexdigest()
        # Verify it's referenced in the v2 report
        referenced = False
        if _REPRO_REPORT_V2.exists():
            referenced = "REPRODUCTION_CHALLENGE" in _REPRO_REPORT_V2.read_text(encoding="utf-8")
        return {
            "ok": True,
            "file": str(_REPRO_CHALLENGE),
            "sha256": sha256,
            "referenced_in_v2_report": referenced,
        }

    # ── C-03: Report covers all v2.0 PRs 1-7 ─────────────────────────────────

    def check_pr_coverage(self) -> dict[str, Any]:
        if not _REPRO_REPORT_V2.exists():
            return {"ok": False, "detail": "REPRODUCTION_REPORT_V2.md missing"}
        content = _REPRO_REPORT_V2.read_text(encoding="utf-8")
        missing = [pr for pr in _REQUIRED_PR_COVERAGE if pr not in content]
        return {
            "ok": not missing,
            "prs_required": len(_REQUIRED_PR_COVERAGE),
            "prs_covered": len(_REQUIRED_PR_COVERAGE) - len(missing),
            "missing_prs": missing,
        }

    # ── C-04: Report covers all 3 governance outcomes ─────────────────────────

    def check_outcome_coverage(self) -> dict[str, Any]:
        if not _REPRO_REPORT_V2.exists():
            return {"ok": False, "detail": "REPRODUCTION_REPORT_V2.md missing"}
        content = _REPRO_REPORT_V2.read_text(encoding="utf-8")
        missing = [o for o in _REQUIRED_OUTCOMES if o not in content]
        return {
            "ok": not missing,
            "outcomes_required": len(_REQUIRED_OUTCOMES),
            "outcomes_covered": len(_REQUIRED_OUTCOMES) - len(missing),
            "missing_outcomes": missing,
        }

    # ── C-05: v2.0 evidence artifact with checksums exists ────────────────────

    def check_evidence_artifact(self) -> dict[str, Any]:
        artifacts = sorted(_REPRO_TOOLS_DIR.glob(_EVIDENCE_GLOB)) if _REPRO_TOOLS_DIR.exists() else []
        if not artifacts:
            return {
                "ok": False,
                "detail": (
                    f"No reproduction_evidence_v2_*.json found in {_REPRO_TOOLS_DIR}. "
                    "Run: python tools/production_readiness/verify_reproduction.py --generate"
                ),
            }
        latest = artifacts[-1]
        try:
            data = json.loads(latest.read_text(encoding="utf-8"))
        except Exception as exc:
            return {"ok": False, "detail": f"Invalid JSON in {latest.name}: {exc}"}

        sha256 = hashlib.sha256(latest.read_bytes()).hexdigest()
        summary = data.get("summary", {})
        subjects_hashed = summary.get("subjects_hashed", 0)
        subjects_total = summary.get("subjects_total", 0)
        return {
            "ok": subjects_hashed >= 15 and subjects_hashed == subjects_total,
            "file": str(latest),
            "sha256": sha256,
            "subjects_hashed": subjects_hashed,
            "subjects_total": subjects_total,
            "pr_coverage": data.get("pr_coverage", ""),
        }

    # ── C-06: Report covers HITL token reproduction ───────────────────────────

    def check_hitl_coverage(self) -> dict[str, Any]:
        if not _REPRO_REPORT_V2.exists():
            return {"ok": False, "detail": "REPRODUCTION_REPORT_V2.md missing"}
        content = _REPRO_REPORT_V2.read_text(encoding="utf-8")
        missing = [t for t in _REQUIRED_HITL_TERMS if t not in content]
        return {
            "ok": not missing,
            "hitl_terms_required": len(_REQUIRED_HITL_TERMS),
            "hitl_terms_present": len(_REQUIRED_HITL_TERMS) - len(missing),
            "missing_terms": missing,
        }

    # ── C-07: Report covers audit chain reproduction ──────────────────────────

    def check_chain_coverage(self) -> dict[str, Any]:
        if not _REPRO_REPORT_V2.exists():
            return {"ok": False, "detail": "REPRODUCTION_REPORT_V2.md missing"}
        content = _REPRO_REPORT_V2.read_text(encoding="utf-8")
        missing = [t for t in _REQUIRED_CHAIN_TERMS if t not in content]
        return {
            "ok": not missing,
            "chain_terms_required": len(_REQUIRED_CHAIN_TERMS),
            "chain_terms_present": len(_REQUIRED_CHAIN_TERMS) - len(missing),
            "missing_terms": missing,
        }

    # ── C-08: Evidence artifact SHA256 fingerprint recorded ───────────────────

    def check_artifact_fingerprint(self) -> dict[str, Any]:
        artifacts = sorted(_REPRO_TOOLS_DIR.glob(_EVIDENCE_GLOB)) if _REPRO_TOOLS_DIR.exists() else []
        if not artifacts:
            return {"ok": False, "detail": "No evidence artifact found"}
        latest = artifacts[-1]
        try:
            data = json.loads(latest.read_text(encoding="utf-8"))
        except Exception as exc:
            return {"ok": False, "detail": str(exc)}
        has_sha = "artifact_sha256" in data
        return {
            "ok": has_sha,
            "file": latest.name,
            "has_artifact_sha256": has_sha,
            "artifact_sha256": data.get("artifact_sha256", ""),
        }

    # ── C-09: External reproducer identity ───────────────────────────────────

    def check_reproducer_id(self) -> dict[str, Any]:
        if not self._reproducer_id:
            return {
                "ok": False,
                "skipped": True,
                "reason": (
                    "AEM_REPRODUCER_ID not set — set to external reproducer identity "
                    "(name or organisation) before claiming external reproduction"
                ),
            }
        return {"ok": True, "reproducer_id": self._reproducer_id}

    # ── C-10: Reproduction date ───────────────────────────────────────────────

    def check_reproduction_date(self) -> dict[str, Any]:
        if not self._reproduction_date:
            return {
                "ok": False,
                "skipped": True,
                "reason": "AEM_REPRODUCTION_DATE not set — set to ISO8601 date of external reproduction",
            }
        return {"ok": True, "reproduction_date": self._reproduction_date}

    # ── Full gate ─────────────────────────────────────────────────────────────

    def gate_check(self) -> dict[str, Any]:
        c01 = self.check_report_v2()
        c02 = self.check_challenge_doc()
        c03 = self.check_pr_coverage()
        c04 = self.check_outcome_coverage()
        c05 = self.check_evidence_artifact()
        c06 = self.check_hitl_coverage()
        c07 = self.check_chain_coverage()
        c08 = self.check_artifact_fingerprint()
        c09 = self.check_reproducer_id()
        c10 = self.check_reproduction_date()

        checks = {
            "C-01_report_v2": c01,
            "C-02_challenge_doc": c02,
            "C-03_pr_coverage": c03,
            "C-04_outcome_coverage": c04,
            "C-05_evidence_artifact": c05,
            "C-06_hitl_coverage": c06,
            "C-07_chain_coverage": c07,
            "C-08_artifact_fingerprint": c08,
            "C-09_reproducer_id": c09,
            "C-10_reproduction_date": c10,
        }

        passed = sum(1 for v in checks.values() if v.get("ok"))
        failed = len(checks) - passed
        status = "PASS" if failed == 0 else "FAIL"

        fail_reason = None
        if status == "FAIL":
            missing_live = []
            if not self._reproducer_id:
                missing_live.append("AEM_REPRODUCER_ID")
            if not self._reproduction_date:
                missing_live.append("AEM_REPRODUCTION_DATE")
            if missing_live:
                fail_reason = (
                    f"External reproduction not yet completed: {', '.join(missing_live)} not set. "
                    "independent_reproduction_claimed=false"
                )
            else:
                failing = [k for k, v in checks.items() if not v.get("ok")]
                fail_reason = f"Failing checks: {', '.join(failing)}"

        return {
            "gate": "EXTERNAL_REPRODUCTION_CHECK",
            "status": status,
            "checks_passed": passed,
            "checks_failed": failed,
            "independent_reproduction_claimed": False,
            "reproducer_id": self._reproducer_id,
            "reproduction_date": self._reproduction_date,
            "fail_reason": fail_reason,
            "checks": checks,
        }
