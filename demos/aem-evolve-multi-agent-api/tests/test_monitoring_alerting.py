"""
Tests for v2.0 PR 5 — Monitoring and alerting evidence gate.

C-01–C-07 pass based on file presence and local metrics introspection.
C-08–C-10 are skipped without AEM_PROMETHEUS_URL.
"""
import sys
from pathlib import Path

import pytest

DEMO_ROOT = Path(__file__).resolve().parents[1]
if str(DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEMO_ROOT))

from monitoring.monitoring_gate import (
    MonitoringGate,
    _REQUIRED_ALERTS,
    _REQUIRED_COUNTERS,
    _REQUIRED_PROM_METRICS,
    _ALERT_RULES_FILE,
    _ALERTMANAGER_CONFIG_FILE,
    _GRAFANA_DASHBOARD_FILE,
)


# ── Gate construction ────────────────────────────────────────────────────────

class TestMonitoringGateInit:
    def test_from_env_returns_gate(self):
        gate = MonitoringGate.from_env()
        assert isinstance(gate, MonitoringGate)

    def test_from_env_no_prometheus_url_when_unset(self, monkeypatch):
        monkeypatch.delenv("AEM_PROMETHEUS_URL", raising=False)
        gate = MonitoringGate.from_env()
        assert gate._prometheus_url is None

    def test_from_env_captures_prometheus_url(self, monkeypatch):
        monkeypatch.setenv("AEM_PROMETHEUS_URL", "http://prometheus.example.com:9090")
        gate = MonitoringGate.from_env()
        assert gate._prometheus_url == "http://prometheus.example.com:9090"


# ── Constants ────────────────────────────────────────────────────────────────

class TestConstants:
    def test_seven_required_alerts(self):
        assert len(_REQUIRED_ALERTS) == 7

    def test_seven_required_counters(self):
        assert len(_REQUIRED_COUNTERS) == 7

    def test_seven_required_prom_metrics(self):
        assert len(_REQUIRED_PROM_METRICS) == 7

    def test_hitl_alert_in_required_alerts(self):
        assert "AEM_HITLApprovalFailed" in _REQUIRED_ALERTS

    def test_kms_alert_in_required_alerts(self):
        assert "AEM_KMSSigningFailed" in _REQUIRED_ALERTS

    def test_oidc_alert_in_required_alerts(self):
        assert "AEM_OIDCProviderOutage" in _REQUIRED_ALERTS

    def test_prom_metrics_have_aem_prefix_and_total_suffix(self):
        for m in _REQUIRED_PROM_METRICS:
            assert m.startswith("aem_"), f"{m} missing aem_ prefix"
            assert m.endswith("_total"), f"{m} missing _total suffix"


# ── C-01: Alert rules YAML ───────────────────────────────────────────────────

class TestAlertRulesCheck:
    def test_alert_rules_file_exists(self):
        assert _ALERT_RULES_FILE.exists(), f"alert_rules.yaml missing at {_ALERT_RULES_FILE}"

    def test_check_returns_ok(self):
        gate = MonitoringGate()
        result = gate.check_alert_rules()
        assert result["ok"] is True

    def test_check_has_sha256(self):
        gate = MonitoringGate()
        result = gate.check_alert_rules()
        assert "sha256" in result
        assert len(result["sha256"]) == 64

    def test_all_seven_alerts_present(self):
        gate = MonitoringGate()
        result = gate.check_alert_rules()
        assert result["alerts_present"] == 7
        assert result["missing_alerts"] == []

    def test_no_missing_prom_metrics(self):
        gate = MonitoringGate()
        result = gate.check_alert_rules()
        assert result["missing_prom_metrics"] == []


# ── C-02: Alertmanager config ────────────────────────────────────────────────

class TestAlertmanagerConfigCheck:
    def test_alertmanager_config_file_exists(self):
        assert _ALERTMANAGER_CONFIG_FILE.exists()

    def test_check_returns_ok(self):
        gate = MonitoringGate()
        result = gate.check_alertmanager_config()
        assert result["ok"] is True

    def test_check_has_receiver_and_route(self):
        gate = MonitoringGate()
        result = gate.check_alertmanager_config()
        assert result["has_receiver"] is True
        assert result["has_route"] is True

    def test_check_has_sha256(self):
        gate = MonitoringGate()
        result = gate.check_alertmanager_config()
        assert len(result["sha256"]) == 64


# ── C-03: Grafana dashboard ──────────────────────────────────────────────────

class TestGrafanaDashboardCheck:
    def test_grafana_dashboard_file_exists(self):
        assert _GRAFANA_DASHBOARD_FILE.exists()

    def test_check_returns_ok(self):
        gate = MonitoringGate()
        result = gate.check_grafana_dashboard()
        assert result["ok"] is True

    def test_seven_or_more_stat_panels(self):
        gate = MonitoringGate()
        result = gate.check_grafana_dashboard()
        assert result["stat_panels"] >= 7

    def test_dashboard_uid_set(self):
        gate = MonitoringGate()
        result = gate.check_grafana_dashboard()
        assert result["dashboard_uid"] == "aem-evolve-governance-v2"

    def test_no_missing_metric_panels(self):
        gate = MonitoringGate()
        result = gate.check_grafana_dashboard()
        assert result["missing_metric_panels"] == []


# ── C-04: Counter registration ───────────────────────────────────────────────

class TestCounterRegistration:
    def test_check_returns_ok(self):
        gate = MonitoringGate()
        result = gate.check_counter_registration()
        assert result["ok"] is True

    def test_all_seven_counters_registered(self):
        gate = MonitoringGate()
        result = gate.check_counter_registration()
        assert len(result["missing_counters"]) == 0
        assert len(result["registered_counters"]) == 7

    def test_hitl_approval_failed_registered(self):
        gate = MonitoringGate()
        result = gate.check_counter_registration()
        assert "hitl_approval_failed" in result["registered_counters"]

    def test_kms_signing_failed_registered(self):
        gate = MonitoringGate()
        result = gate.check_counter_registration()
        assert "kms_signing_failed" in result["registered_counters"]


# ── C-05: Counter name consistency ───────────────────────────────────────────

class TestCounterNameConsistency:
    def test_check_returns_ok(self):
        gate = MonitoringGate()
        result = gate.check_counter_name_consistency()
        assert result["ok"] is True

    def test_no_mismatches(self):
        gate = MonitoringGate()
        result = gate.check_counter_name_consistency()
        assert result["mismatches"] == []

    def test_all_pairs_checked(self):
        gate = MonitoringGate()
        result = gate.check_counter_name_consistency()
        assert result["checked_pairs"] == 7


# ── C-06: Metrics endpoint ───────────────────────────────────────────────────

class TestMetricsEndpoint:
    def test_check_returns_ok(self):
        gate = MonitoringGate()
        result = gate.check_metrics_endpoint()
        assert result["ok"] is True

    def test_metrics_endpoint_present_in_main(self):
        gate = MonitoringGate()
        result = gate.check_metrics_endpoint()
        assert result["metrics_endpoint_present"] is True

    def test_all_counters_wired_in_code(self):
        gate = MonitoringGate()
        result = gate.check_metrics_endpoint()
        assert result["counters_not_yet_wired"] == [], (
            f"Counters not wired in main.py: {result['counters_not_yet_wired']}"
        )


# ── C-07: Receiver configured ────────────────────────────────────────────────

class TestReceiverConfigured:
    def test_check_returns_ok(self):
        gate = MonitoringGate()
        result = gate.check_receiver_configured()
        assert result["ok"] is True

    def test_email_or_slack_configured(self):
        gate = MonitoringGate()
        result = gate.check_receiver_configured()
        assert result["email_configured"] or result["slack_configured"]


# ── C-08–C-10: Live Prometheus (skipped without AEM_PROMETHEUS_URL) ──────────

class TestLivePrometheusChecks:
    def test_prometheus_reachable_skipped_without_url(self, monkeypatch):
        monkeypatch.delenv("AEM_PROMETHEUS_URL", raising=False)
        gate = MonitoringGate(prometheus_url=None)
        result = gate.check_prometheus_reachable()
        assert result.get("skipped") is True
        assert result["ok"] is False

    def test_alert_rules_loaded_skipped_without_url(self, monkeypatch):
        monkeypatch.delenv("AEM_PROMETHEUS_URL", raising=False)
        gate = MonitoringGate(prometheus_url=None)
        result = gate.check_alert_rules_loaded()
        assert result.get("skipped") is True

    def test_alert_can_fire_skipped_without_url(self, monkeypatch):
        monkeypatch.delenv("AEM_PROMETHEUS_URL", raising=False)
        gate = MonitoringGate(prometheus_url=None)
        result = gate.check_alert_can_fire()
        assert result.get("skipped") is True


# ── Full gate_check ───────────────────────────────────────────────────────────

class TestGateCheck:
    def test_gate_check_has_required_fields(self):
        gate = MonitoringGate()
        result = gate.gate_check()
        assert result["gate"] == "MONITORING_ALERTING_CHECK"
        assert result["status"] in ("PASS", "FAIL")
        assert "checks_passed" in result
        assert "checks_failed" in result
        assert "checks" in result

    def test_gate_check_fails_without_prometheus(self, monkeypatch):
        monkeypatch.delenv("AEM_PROMETHEUS_URL", raising=False)
        gate = MonitoringGate(prometheus_url=None)
        result = gate.gate_check()
        assert result["status"] == "FAIL"
        assert result["prometheus_url_configured"] is False

    def test_gate_check_seven_config_checks_pass(self, monkeypatch):
        monkeypatch.delenv("AEM_PROMETHEUS_URL", raising=False)
        gate = MonitoringGate(prometheus_url=None)
        result = gate.gate_check()
        checks = result["checks"]
        config_keys = [k for k in checks if k.startswith(("C-01", "C-02", "C-03", "C-04", "C-05", "C-06", "C-07"))]
        passed_config = sum(1 for k in config_keys if checks[k].get("ok"))
        assert passed_config == 7, f"Expected 7 config checks to pass, got {passed_config}: {checks}"

    def test_gate_check_fail_reason_mentions_prometheus(self, monkeypatch):
        monkeypatch.delenv("AEM_PROMETHEUS_URL", raising=False)
        gate = MonitoringGate(prometheus_url=None)
        result = gate.gate_check()
        assert result.get("fail_reason") is not None
        assert "AEM_PROMETHEUS_URL" in result["fail_reason"]


# ── Health endpoint ───────────────────────────────────────────────────────────

class TestHealthMonitoringGate:
    def test_monitoring_alerting_gate_in_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "monitoring_alerting_gate" in data

    def test_monitoring_gate_has_required_fields(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        gate = resp.json()["monitoring_alerting_gate"]
        assert gate["gate"] == "MONITORING_ALERTING_CHECK"
        assert "status" in gate

    def test_version_bumped_to_pr5(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["version"] == "0.19.0-demo"
