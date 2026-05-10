"""
Fast-path pytest tests for v1.9.0 materiality parametrization:
all three governance paths (FAIL_CLOSED, SCOPE_LIMITED, PASS) reachable via StartRequest.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.conftest import client, INITIATOR_KEY, OBSERVER_KEY, unique_tid


def _start(client, materiality: float):
    tid = unique_tid()
    r = client.post("/start", json={"thread_id": tid, "materiality_score": materiality},
                    headers={"X-API-Key": INITIATOR_KEY})
    return tid, r


class TestMaterialityPaths:
    def test_fail_closed_path(self, client):
        _, r = _start(client, 90.0)
        assert r.status_code == 200
        assert r.json()["status"] == "completed_fail_closed"

    def test_scope_limited_path(self, client):
        _, r = _start(client, 78.0)
        assert r.status_code == 200
        assert r.json()["status"] == "awaiting_human_approval"

    def test_pass_path(self, client):
        _, r = _start(client, 50.0)
        assert r.status_code == 200
        assert r.json()["status"] == "completed"

    def test_fail_closed_receipt_outcome(self, client):
        tid, _ = _start(client, 90.0)
        rec = client.get(f"/receipt/{tid}", headers={"X-API-Key": OBSERVER_KEY}).json()
        assert rec["receipt_payload"]["outcome"] == "FAIL_CLOSED"

    def test_scope_limited_receipt_outcome(self, client):
        tid, _ = _start(client, 78.0)
        rec = client.get(f"/receipt/{tid}", headers={"X-API-Key": OBSERVER_KEY}).json()
        assert rec["receipt_payload"]["outcome"] == "SCOPE_LIMITED"

    def test_pass_receipt_outcome(self, client):
        tid, _ = _start(client, 50.0)
        rec = client.get(f"/receipt/{tid}", headers={"X-API-Key": OBSERVER_KEY}).json()
        assert rec["receipt_payload"]["outcome"] == "PASS"

    def test_materiality_above_100_rejected(self, client):
        r = client.post("/start", json={"thread_id": unique_tid(), "materiality_score": 101.0},
                        headers={"X-API-Key": INITIATOR_KEY})
        assert r.status_code == 422

    def test_materiality_below_0_rejected(self, client):
        r = client.post("/start", json={"thread_id": unique_tid(), "materiality_score": -1.0},
                        headers={"X-API-Key": INITIATOR_KEY})
        assert r.status_code == 422

    def test_health_materiality_parametrized(self, client):
        body = client.get("/health").json()
        assert body.get("materiality_parametrized") is True

    def test_health_governance_paths(self, client):
        body = client.get("/health").json()
        paths = body.get("governance_paths", [])
        assert "FAIL_CLOSED" in paths
        assert "SCOPE_LIMITED" in paths
        assert "PASS" in paths
