"""
Integration tests for AEM-EVOLVE API endpoints.
Runs against the TestClient using real SQLite storage.
"""
import hashlib
import hmac
import math
import time
import pytest
from .conftest import (
    client,
    INITIATOR_KEY,
    APPROVER_KEY,
    OBSERVER_KEY,
    UNKNOWN_KEY,
    unique_tid,
)

_HITL_SECRET = "ethicbit-hitl-demo-secret-v1.4"
_HITL_APPROVER = "approver-001"


def _make_hitl_token(approver_id: str, event_id: str, secret: str = _HITL_SECRET) -> str:
    ts_floor = math.floor(time.time() / 60)
    payload = f"{approver_id}:{event_id}:{ts_floor}".encode()
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


class TestHealth:
    def test_health_returns_200(self, client):
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_body(self, client):
        body = client.get("/health").json()
        assert body["status"] == "healthy"
        assert body["version"] == "0.14.0-demo"
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
        assert body["version"] == "0.14.0-demo"


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
    def _start_and_get_event_id(self, client):
        """Start a session and return (thread_id, event_id) for HITL token generation."""
        tid = unique_tid()
        client.post("/start", json={"thread_id": tid}, headers={"X-API-Key": INITIATOR_KEY})
        receipt = client.get(f"/receipt/{tid}", headers={"X-API-Key": OBSERVER_KEY}).json()
        event_id = receipt["event_id"]
        return tid, event_id

    def test_approve_decision(self, client):
        tid, event_id = self._start_and_get_event_id(client)
        token = _make_hitl_token(_HITL_APPROVER, event_id)
        r = client.post("/approve",
                        json={"thread_id": tid, "decision": "approve", "override_reason": "test",
                              "hitl_token": token, "hitl_approver_id": _HITL_APPROVER},
                        headers={"X-API-Key": APPROVER_KEY})
        assert r.status_code == 200
        assert r.json()["status"] in ("completed", "change_human_approved", "completed_approved")

    def test_reject_decision(self, client):
        tid, event_id = self._start_and_get_event_id(client)
        token = _make_hitl_token(_HITL_APPROVER, event_id)
        r = client.post("/approve",
                        json={"thread_id": tid, "decision": "reject",
                              "hitl_token": token, "hitl_approver_id": _HITL_APPROVER},
                        headers={"X-API-Key": APPROVER_KEY})
        assert r.status_code == 200
        assert "rejected" in r.json()["status"]

    def test_approve_requires_approver_role(self, client):
        tid, event_id = self._start_and_get_event_id(client)
        token = _make_hitl_token(_HITL_APPROVER, event_id)
        r = client.post("/approve",
                        json={"thread_id": tid, "decision": "approve",
                              "hitl_token": token, "hitl_approver_id": _HITL_APPROVER},
                        headers={"X-API-Key": INITIATOR_KEY})
        assert r.status_code == 403

    def test_approve_missing_token_returns_400(self, client):
        tid, _ = self._start_and_get_event_id(client)
        r = client.post("/approve",
                        json={"thread_id": tid, "decision": "approve"},
                        headers={"X-API-Key": APPROVER_KEY})
        assert r.status_code == 400

    def test_approve_invalid_token_returns_403(self, client):
        tid, event_id = self._start_and_get_event_id(client)
        r = client.post("/approve",
                        json={"thread_id": tid, "decision": "approve",
                              "hitl_token": "deadbeef" * 8, "hitl_approver_id": _HITL_APPROVER},
                        headers={"X-API-Key": APPROVER_KEY})
        assert r.status_code == 403

    def test_approve_no_pending_returns_400(self, client):
        r = client.post("/approve",
                        json={"thread_id": "t-nopending123", "decision": "approve"},
                        headers={"X-API-Key": APPROVER_KEY})
        assert r.status_code in (400, 404)

    def test_approve_replay_returns_409(self, client):
        tid, event_id = self._start_and_get_event_id(client)
        token = _make_hitl_token(_HITL_APPROVER, event_id)
        r1 = client.post("/approve",
                         json={"thread_id": tid, "decision": "approve",
                               "hitl_token": token, "hitl_approver_id": _HITL_APPROVER},
                         headers={"X-API-Key": APPROVER_KEY})
        assert r1.status_code == 200
        # Second call with same token must be rejected — no pending approval exists now,
        # but the 409 replay guard fires before the 400 no-pending guard only if the
        # session still has human_approval_needed. Start a fresh session to test replay.
        tid2, event_id2 = self._start_and_get_event_id(client)
        # Reuse same token bytes but for the new event_id — this token is valid for event_id2
        # only if we generate it for event_id2. Test with the SAME token against event_id2
        # to verify cross-event tokens are rejected at the 403 layer.
        # To specifically test replay: start another session that reuses the EXACT same event_id
        # (not possible; event_ids are UUIDs). Instead test that a second approve on event_id
        # fails once the session is consumed (400 no-pending), which is covered above.
        # Replay guard test: patch the used_tokens table directly.
        from main import db_adapter as _da, _is_token_used, _mark_token_used
        import hashlib as _hl
        token3 = _make_hitl_token(_HITL_APPROVER, event_id2)
        # Pre-mark token3 as used
        _mark_token_used(token3, event_id2, _HITL_APPROVER, _da)
        assert _is_token_used(token3, event_id2, _da)
        r2 = client.post("/approve",
                         json={"thread_id": tid2, "decision": "approve",
                               "hitl_token": token3, "hitl_approver_id": _HITL_APPROVER},
                         headers={"X-API-Key": APPROVER_KEY})
        assert r2.status_code == 409


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
