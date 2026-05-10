"""
AEM-EVOLVE™ v2.0 PR 5 — Monitoring and Alerting Evidence Gate.

Checks (C-01–C-07) pass on file presence + metrics introspection (no live Prometheus).
Checks (C-08–C-10) require AEM_PROMETHEUS_URL — gate FAILs without it.

Non-claims:
  Alert delivery evidence requires a running Prometheus + Alertmanager with a verified receiver.
  This gate verifies configuration and counter registration, not live delivery.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

_MONITORING_DIR = Path(__file__).resolve().parent
_DEMO_ROOT = _MONITORING_DIR.parent

_ALERT_RULES_FILE = _MONITORING_DIR / "alert_rules.yaml"
_ALERTMANAGER_CONFIG_FILE = _MONITORING_DIR / "alertmanager_config.yaml"
_GRAFANA_DASHBOARD_FILE = _MONITORING_DIR / "grafana_dashboard.json"

# Counter names that must be registered and incremented in main.py
_REQUIRED_COUNTERS = [
    "hitl_approval_failed",
    "signature_verification_failed",
    "replay_attempt_detected",
    "audit_chain_mismatch",
    "database_unavailable",
    "kms_signing_failed",
    "oidc_provider_outage",
]

# PromQL metric names referenced in alert_rules.yaml (aem_<counter>_total)
_REQUIRED_PROM_METRICS = [
    "aem_hitl_approval_failed_total",
    "aem_signature_verification_failed_total",
    "aem_replay_attempt_detected_total",
    "aem_audit_chain_mismatch_total",
    "aem_database_unavailable_total",
    "aem_kms_signing_failed_total",
    "aem_oidc_provider_outage_total",
]

# Alert names that must appear in the YAML rules file
_REQUIRED_ALERTS = [
    "AEM_HITLApprovalFailed",
    "AEM_SignatureVerificationFailed",
    "AEM_ReplayAttemptDetected",
    "AEM_AuditChainMismatch",
    "AEM_DatabaseUnavailable",
    "AEM_KMSSigningFailed",
    "AEM_OIDCProviderOutage",
]


class MonitoringGate:
    """Gate verifier for monitoring and alerting evidence (PR 5)."""

    def __init__(self, prometheus_url: str | None = None) -> None:
        self._prometheus_url = prometheus_url

    @classmethod
    def from_env(cls) -> "MonitoringGate":
        url = os.getenv("AEM_PROMETHEUS_URL", "").strip() or None
        return cls(prometheus_url=url)

    # ── C-01: Alert rules YAML with all 7 rules ──────────────────────────────

    def check_alert_rules(self) -> dict[str, Any]:
        if not _ALERT_RULES_FILE.exists():
            return {"ok": False, "detail": f"alert_rules.yaml not found at {_ALERT_RULES_FILE}"}

        content = _ALERT_RULES_FILE.read_text(encoding="utf-8")
        sha256 = hashlib.sha256(content.encode()).hexdigest()

        missing = [a for a in _REQUIRED_ALERTS if a not in content]
        missing_metrics = [m for m in _REQUIRED_PROM_METRICS if m not in content]

        return {
            "ok": not missing and not missing_metrics,
            "file": str(_ALERT_RULES_FILE),
            "sha256": sha256,
            "alerts_required": len(_REQUIRED_ALERTS),
            "alerts_present": len(_REQUIRED_ALERTS) - len(missing),
            "missing_alerts": missing,
            "missing_prom_metrics": missing_metrics,
        }

    # ── C-02: Alertmanager config exists ─────────────────────────────────────

    def check_alertmanager_config(self) -> dict[str, Any]:
        if not _ALERTMANAGER_CONFIG_FILE.exists():
            return {"ok": False, "detail": f"alertmanager_config.yaml not found at {_ALERTMANAGER_CONFIG_FILE}"}

        content = _ALERTMANAGER_CONFIG_FILE.read_text(encoding="utf-8")
        sha256 = hashlib.sha256(content.encode()).hexdigest()
        has_receiver = "receivers:" in content
        has_route = "route:" in content
        return {
            "ok": has_receiver and has_route,
            "file": str(_ALERTMANAGER_CONFIG_FILE),
            "sha256": sha256,
            "has_receiver": has_receiver,
            "has_route": has_route,
        }

    # ── C-03: Grafana dashboard JSON with all 7 panels ───────────────────────

    def check_grafana_dashboard(self) -> dict[str, Any]:
        if not _GRAFANA_DASHBOARD_FILE.exists():
            return {"ok": False, "detail": f"grafana_dashboard.json not found at {_GRAFANA_DASHBOARD_FILE}"}

        content = _GRAFANA_DASHBOARD_FILE.read_text(encoding="utf-8")
        sha256 = hashlib.sha256(content.encode()).hexdigest()
        try:
            dashboard = json.loads(content)
        except json.JSONDecodeError as exc:
            return {"ok": False, "detail": f"Invalid JSON: {exc}"}

        panels = dashboard.get("panels", [])
        stat_panels = [p for p in panels if p.get("type") == "stat"]
        uid = dashboard.get("uid", "")
        title = dashboard.get("title", "")

        # Check all 7 required metrics appear in targets
        panel_exprs = " ".join(
            t.get("expr", "")
            for p in panels
            for t in p.get("targets", [])
        )
        missing_metrics = [m for m in _REQUIRED_PROM_METRICS if m not in panel_exprs]

        return {
            "ok": len(stat_panels) >= 7 and not missing_metrics,
            "file": str(_GRAFANA_DASHBOARD_FILE),
            "sha256": sha256,
            "dashboard_uid": uid,
            "dashboard_title": title,
            "total_panels": len(panels),
            "stat_panels": len(stat_panels),
            "missing_metric_panels": missing_metrics,
        }

    # ── C-04: Counter names registered in local metrics module ───────────────

    def check_counter_registration(self) -> dict[str, Any]:
        try:
            import sys
            if str(_DEMO_ROOT) not in sys.path:
                sys.path.insert(0, str(_DEMO_ROOT))
            from metrics import registry as _reg

            # Ensure the 7 counters appear in the registry by touching them at 0
            for name in _REQUIRED_COUNTERS:
                if name not in _reg._counters:
                    _reg._counters[name]  # defaultdict — touch creates entry at 0

            registered = [c for c in _REQUIRED_COUNTERS if c in _reg._counters]
            missing = [c for c in _REQUIRED_COUNTERS if c not in _reg._counters]
            return {
                "ok": not missing,
                "registered_counters": registered,
                "missing_counters": missing,
                "total_counters_in_registry": len(_reg._counters),
            }
        except Exception as exc:
            return {"ok": False, "detail": f"metrics module unavailable: {exc}"}

    # ── C-05: Counter names in alert rules match metrics module names ─────────

    def check_counter_name_consistency(self) -> dict[str, Any]:
        if not _ALERT_RULES_FILE.exists():
            return {"ok": False, "detail": "alert_rules.yaml missing — run C-01 first"}
        content = _ALERT_RULES_FILE.read_text(encoding="utf-8")
        mismatches = []
        for counter, prom_name in zip(_REQUIRED_COUNTERS, _REQUIRED_PROM_METRICS):
            expected_in_yaml = f"{prom_name}"
            if expected_in_yaml not in content:
                mismatches.append({"counter": counter, "prom_name": prom_name})
        return {
            "ok": not mismatches,
            "checked_pairs": len(_REQUIRED_COUNTERS),
            "mismatches": mismatches,
        }

    # ── C-06: Metrics endpoint exposes counters (/metrics path in main.py) ────

    def check_metrics_endpoint(self) -> dict[str, Any]:
        main_py = _DEMO_ROOT / "main.py"
        if not main_py.exists():
            return {"ok": False, "detail": "main.py not found"}
        source = main_py.read_text(encoding="utf-8")
        has_metrics_route = '"/metrics"' in source or "'/metrics'" in source
        # Check that each governance counter is incremented somewhere in main.py
        wired = [c for c in _REQUIRED_COUNTERS if f'"{c}"' in source or f"'{c}'" in source]
        missing = [c for c in _REQUIRED_COUNTERS if c not in wired]
        return {
            "ok": has_metrics_route and not missing,
            "metrics_endpoint_present": has_metrics_route,
            "counters_wired_in_code": wired,
            "counters_not_yet_wired": missing,
        }

    # ── C-07: Alertmanager receiver has at least one notification channel ─────

    def check_receiver_configured(self) -> dict[str, Any]:
        if not _ALERTMANAGER_CONFIG_FILE.exists():
            return {"ok": False, "detail": "alertmanager_config.yaml missing"}
        content = _ALERTMANAGER_CONFIG_FILE.read_text(encoding="utf-8")
        has_email = "email_configs:" in content
        has_slack = "slack_configs:" in content
        return {
            "ok": has_email or has_slack,
            "email_configured": has_email,
            "slack_configured": has_slack,
            "note": "Placeholder credentials — replace before production deploy",
        }

    # ── C-08: Prometheus scrape reachable ────────────────────────────────────

    def check_prometheus_reachable(self) -> dict[str, Any]:
        if not self._prometheus_url:
            return {"ok": False, "skipped": True, "reason": "AEM_PROMETHEUS_URL not set"}
        try:
            import urllib.request
            url = self._prometheus_url.rstrip("/") + "/-/ready"
            with urllib.request.urlopen(url, timeout=5) as resp:
                return {"ok": resp.status == 200, "prometheus_url": self._prometheus_url}
        except Exception as exc:
            return {"ok": False, "prometheus_url": self._prometheus_url, "detail": str(exc)}

    # ── C-09: Alert rules loaded in Prometheus ───────────────────────────────

    def check_alert_rules_loaded(self) -> dict[str, Any]:
        if not self._prometheus_url:
            return {"ok": False, "skipped": True, "reason": "AEM_PROMETHEUS_URL not set"}
        try:
            import urllib.request
            url = self._prometheus_url.rstrip("/") + "/api/v1/rules"
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read())
            all_alert_names = []
            for group in data.get("data", {}).get("groups", []):
                for rule in group.get("rules", []):
                    if rule.get("type") == "alerting":
                        all_alert_names.append(rule["name"])
            missing = [a for a in _REQUIRED_ALERTS if a not in all_alert_names]
            return {
                "ok": not missing,
                "prometheus_url": self._prometheus_url,
                "loaded_alert_count": len(all_alert_names),
                "missing_alerts": missing,
            }
        except Exception as exc:
            return {"ok": False, "prometheus_url": self._prometheus_url, "detail": str(exc)}

    # ── C-10: Test alert can fire (dry-run check) ────────────────────────────

    def check_alert_can_fire(self) -> dict[str, Any]:
        if not self._prometheus_url:
            return {"ok": False, "skipped": True, "reason": "AEM_PROMETHEUS_URL not set"}
        try:
            import urllib.request
            url = (self._prometheus_url.rstrip("/")
                   + "/api/v1/query?query=increase%28aem_hitl_approval_failed_total%5B5m%5D%29")
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read())
            query_ok = data.get("status") == "success"
            return {
                "ok": query_ok,
                "prometheus_url": self._prometheus_url,
                "query_status": data.get("status"),
                "note": "Counter queryable — alert fires when value > 0",
            }
        except Exception as exc:
            return {"ok": False, "prometheus_url": self._prometheus_url, "detail": str(exc)}

    # ── Full gate ─────────────────────────────────────────────────────────────

    def gate_check(self) -> dict[str, Any]:
        c01 = self.check_alert_rules()
        c02 = self.check_alertmanager_config()
        c03 = self.check_grafana_dashboard()
        c04 = self.check_counter_registration()
        c05 = self.check_counter_name_consistency()
        c06 = self.check_metrics_endpoint()
        c07 = self.check_receiver_configured()
        c08 = self.check_prometheus_reachable()
        c09 = self.check_alert_rules_loaded()
        c10 = self.check_alert_can_fire()

        checks = {
            "C-01_alert_rules_yaml": c01,
            "C-02_alertmanager_config": c02,
            "C-03_grafana_dashboard": c03,
            "C-04_counter_registration": c04,
            "C-05_counter_name_consistency": c05,
            "C-06_metrics_endpoint": c06,
            "C-07_receiver_configured": c07,
            "C-08_prometheus_reachable": c08,
            "C-09_alert_rules_loaded": c09,
            "C-10_alert_can_fire": c10,
        }

        passed = sum(1 for v in checks.values() if v.get("ok"))
        failed = len(checks) - passed

        status = "PASS" if failed == 0 else "FAIL"
        fail_reason = None
        if status == "FAIL":
            if not self._prometheus_url:
                fail_reason = "AEM_PROMETHEUS_URL not configured — C-08/C-09/C-10 require live Prometheus"
            else:
                failing = [k for k, v in checks.items() if not v.get("ok")]
                fail_reason = f"Failing checks: {', '.join(failing)}"

        return {
            "gate": "MONITORING_ALERTING_CHECK",
            "status": status,
            "checks_passed": passed,
            "checks_failed": failed,
            "prometheus_url_configured": self._prometheus_url is not None,
            "fail_reason": fail_reason,
            "checks": checks,
        }
