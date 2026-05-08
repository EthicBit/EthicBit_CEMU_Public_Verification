"""
Tests for RBAC authentication and authorization.
"""
import pytest
from .conftest import client, INITIATOR_KEY, APPROVER_KEY, OBSERVER_KEY, UNKNOWN_KEY


class TestMissingKey:
    def test_start_no_key(self, client):
        r = client.post("/start", json={"thread_id": "t-nokey-start"})
        assert r.status_code == 401

    def test_approve_no_key(self, client):
        r = client.post("/approve", json={"thread_id": "t-nokey", "decision": "approve"})
        assert r.status_code == 401

    def test_status_no_key(self, client):
        r = client.get("/status/some-thread")
        assert r.status_code == 401

    def test_metrics_no_key(self, client):
        r = client.get("/metrics")
        assert r.status_code == 401

    def test_receipt_no_key(self, client):
        r = client.get("/receipt/some-thread")
        assert r.status_code == 401


class TestUnknownKey:
    def test_start_unknown_key(self, client):
        r = client.post("/start",
                        json={"thread_id": "t-unk"},
                        headers={"X-API-Key": UNKNOWN_KEY})
        assert r.status_code == 401

    def test_metrics_unknown_key(self, client):
        r = client.get("/metrics", headers={"X-API-Key": UNKNOWN_KEY})
        assert r.status_code == 401


class TestWrongRole:
    def test_approver_cannot_start(self, client):
        r = client.post("/start",
                        json={"thread_id": "t-wrongrole"},
                        headers={"X-API-Key": APPROVER_KEY})
        assert r.status_code == 403

    def test_observer_cannot_start(self, client):
        r = client.post("/start",
                        json={"thread_id": "t-wrongrole2"},
                        headers={"X-API-Key": OBSERVER_KEY})
        assert r.status_code == 403

    def test_initiator_cannot_approve(self, client):
        r = client.post("/approve",
                        json={"thread_id": "t-wrongrole3", "decision": "approve"},
                        headers={"X-API-Key": INITIATOR_KEY})
        assert r.status_code == 403


class TestValidKeys:
    def test_health_no_auth_required(self, client):
        r = client.get("/health")
        assert r.status_code == 200

    def test_healthz_no_auth_required(self, client):
        r = client.get("/healthz")
        assert r.status_code == 200

    def test_observer_can_read_metrics(self, client):
        r = client.get("/metrics", headers={"X-API-Key": OBSERVER_KEY})
        assert r.status_code == 200

    def test_initiator_can_read_metrics(self, client):
        r = client.get("/metrics", headers={"X-API-Key": INITIATOR_KEY})
        assert r.status_code == 200
