"""
Integration tests for AEM-EVOLVE API endpoints.
Runs against the TestClient using real SQLite storage.
"""
import pytest
from .conftest import (
    client,
    INITIATOR_KEY,
    APPROVER_KEY,
    OBSERVER_KEY,
    UNKNOWN_KEY,
    unique_tid,
)


class TestHealth:
    def test_health_returns_200(self, client):
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_body(self, client):
        body = client.get("/health").json()
        assert body["status"] == "healthy"
        assert body["version"] == "0.3.1-demo"
        assert body["tamper_proof_claimed"] is False
        assert "non_claims" in body

    def test_healthz_returns_200(self, client):
        r = client.get("/healthz")
        assert r.status_code == 200

    def test_healthz_db_ok(self, client):
        body = client.get("/healthz").json()
        assert body["status"] == "ok"
        assert body["db"] == "sqlite"

    def test_healthz_version(self, client):
        body = client.get("/healthz").json()
        assert body["version"] == "0.3.1-demo"


class TestMetricsEndpoint:
    def test_metrics_requires_auth(self, client):
        assert client.get("/metrics").status_code == 401

    def test_metrics_observer_ok(self, client):
        r = client.get("/metrics", headers={"X-API-Key": OBSERVER_KEY})
        assert r.status_code == 200

    def test_metrics_has_counters_and_timings(self, client):
        body = client.get("/metrics", headers={"X-API-Key": OBSERVER_KEY}).json()
        assert "counters" in body
        assert "timings" in body


class TestStartEndpoint:
    def test_start_success(self, client):
        tid = unique_tid()
        r = client.post("/start",
                        json={"thread_id": tid, "initial_prompt": "Test prompt"},
                        headers={"X-API-Key": INITIATOR_KEY})
        assert r.status_code == 200
        body = r.json()
        assert body["thread_id"] == tid
        assert "status" in body

    def test_start_sets_awaiting_approval(self, client):
        # Default materiality=78 always produces SCOPE_LIMITED → awaiting_human_approval
        tid = unique_tid()
        r = client.post("/start",
                        json={"thread_id": tid},
                        headers={"X-API-Key": INITIATOR_KEY})
        assert r.status_code == 200
        assert r.json()["status"] == "awaiting_human_approval"

    def test_start_rejects_invalid_thread_id(self, client):
        r = client.post("/start",
                        json={"thread_id": "invalid id with spaces!", "initial_prompt": "x"},
                        headers={"X-API-Key": INITIATOR_KEY})
        assert r.status_code == 422

    def test_start_rejects_oversized_prompt(self, client):
        r = client.post("/start",
                        json={"thread_id": unique_tid(), "initial_prompt": "x" * 4097},
                        headers={"X-API-Key": INITIATOR_KEY})
        assert r.status_code == 422

    def test_start_increments_sessions_counter(self, client):
        before = client.get("/metrics", headers={"X-API-Key": OBSERVER_KEY}).json()
        before_count = before["counters"].get("sessions_started", 0)
        client.post("/start",
                    json={"thread_id": unique_tid()},
                    headers={"X-API-Key": INITIATOR_KEY})
        after = client.get("/metrics", headers={"X-API-Key": OBSERVER_KEY}).json()
        assert after["counters"]["sessions_started"] == before_count + 1


class TestStatusEndpoint:
    def test_status_after_start(self, client):
        tid = unique_tid()
        client.post("/start", json={"thread_id": tid}, headers={"X-API-Key": INITIATOR_KEY})
        r = client.get(f"/status/{tid}", headers={"X-API-Key": OBSERVER_KEY})
        assert r.status_code == 200
        body = r.json()
        assert body["thread_id"] == tid
        assert "status" in body
        assert "human_approval_needed" in body

    def test_status_requires_auth(self, client):
        r = client.get("/status/some-thread")
        assert r.status_code == 401


class TestReceiptEndpoint:
    def test_receipt_after_start(self, client):
        tid = unique_tid()
        client.post("/start", json={"thread_id": tid}, headers={"X-API-Key": INITIATOR_KEY})
        r = client.get(f"/receipt/{tid}", headers={"X-API-Key": OBSERVER_KEY})
        assert r.status_code == 200
        body = r.json()
        assert "receipt_payload" in body
        assert body["receipt_payload"]["outcome"] == "SCOPE_LIMITED"

    def test_receipt_requires_auth(self, client):
        assert client.get("/receipt/some-thread").status_code == 401


class TestApproveEndpoint:
    def _start_session(self, client):
        tid = unique_tid()
        client.post("/start", json={"thread_id": tid}, headers={"X-API-Key": INITIATOR_KEY})
        return tid

    def test_approve_decision(self, client):
        tid = self._start_session(client)
        r = client.post("/approve",
                        json={"thread_id": tid, "decision": "approve", "override_reason": "test"},
                        headers={"X-API-Key": APPROVER_KEY})
        assert r.status_code == 200
        assert r.json()["status"] in ("completed", "change_human_approved", "completed_approved")

    def test_reject_decision(self, client):
        tid = self._start_session(client)
        r = client.post("/approve",
                        json={"thread_id": tid, "decision": "reject"},
                        headers={"X-API-Key": APPROVER_KEY})
        assert r.status_code == 200
        assert "rejected" in r.json()["status"]

    def test_approve_requires_approver_role(self, client):
        tid = self._start_session(client)
        r = client.post("/approve",
                        json={"thread_id": tid, "decision": "approve"},
                        headers={"X-API-Key": INITIATOR_KEY})
        assert r.status_code == 403

    def test_approve_no_pending_returns_400(self, client):
        # Thread that hasn't started has no pending approval.
        r = client.post("/approve",
                        json={"thread_id": "t-nopending123", "decision": "approve"},
                        headers={"X-API-Key": APPROVER_KEY})
        # Either 400 (no approval needed) or 404 (thread not found)
        assert r.status_code in (400, 404)


class TestAuditEndpoint:
    def test_audit_after_start(self, client):
        tid = unique_tid()
        client.post("/start", json={"thread_id": tid}, headers={"X-API-Key": INITIATOR_KEY})
        r = client.get(f"/audit/{tid}", headers={"X-API-Key": OBSERVER_KEY})
        assert r.status_code == 200
        body = r.json()
        assert body["thread_id"] == tid
        assert len(body["events"]) >= 1
        assert len(body["receipts"]) >= 1

    def test_audit_requires_auth(self, client):
        assert client.get("/audit/any-thread").status_code == 401


class TestChainEndpoint:
    def test_chain_verify_returns_status(self, client):
        r = client.get("/chain/verify", headers={"X-API-Key": OBSERVER_KEY})
        assert r.status_code == 200
        body = r.json()
        assert body["status"] in ("PASS", "EMPTY", "TAMPER_DETECTED")
        assert "entries_checked" in body

    def test_chain_verify_tamper_evident_flag(self, client):
        body = client.get("/chain/verify", headers={"X-API-Key": OBSERVER_KEY}).json()
        assert body.get("tamper_evident") is True
        assert body.get("tamper_proof_claimed") is False

    def test_chain_for_thread(self, client):
        tid = unique_tid()
        client.post("/start", json={"thread_id": tid}, headers={"X-API-Key": INITIATOR_KEY})
        r = client.get(f"/chain/{tid}", headers={"X-API-Key": OBSERVER_KEY})
        assert r.status_code == 200
        body = r.json()
        assert body["thread_id"] == tid
        assert body["count"] >= 2  # at least event + receipt entries
