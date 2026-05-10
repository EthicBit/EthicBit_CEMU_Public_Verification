"""
Fast-path pytest tests for v1.8.0 OIDC HITL wiring:
dual-path approval (HMAC hex | OIDC JWT), /oidc/jwks endpoint.
"""
import hashlib
import hmac
import math
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import main as _main
from tests.conftest import (
    client,
    INITIATOR_KEY,
    APPROVER_KEY,
    OBSERVER_KEY,
    unique_tid,
)

_HITL_SECRET = "ethicbit-hitl-demo-secret-v1.4"
_HITL_APPROVER = "approver-001"


def _make_hmac_token(approver_id: str, event_id: str) -> str:
    ts_floor = math.floor(time.time() / 60)
    payload = f"{approver_id}:{event_id}:{ts_floor}".encode()
    return hmac.new(_HITL_SECRET.encode(), payload, hashlib.sha256).hexdigest()


def _make_oidc_token(approver_id: str, event_id: str) -> str:
    from hitl.oidc_token_generator import generate_token
    kp = _main._oidc_key_pair
    policy = _main._OIDC_POLICY
    return generate_token(
        kp, sub=approver_id, event_id=event_id,
        issuer=policy.get("issuer", "https://hitl.ethicbit.internal"),
        audience=policy.get("audience", "aem-evolve-hitl"),
    )


def _start_and_get_event_id(client):
    tid = unique_tid()
    client.post("/start", json={"thread_id": tid}, headers={"X-API-Key": INITIATOR_KEY})
    receipt = client.get(f"/receipt/{tid}", headers={"X-API-Key": OBSERVER_KEY}).json()
    return tid, receipt.get("event_id", "")


class TestOIDCProviderInit:
    def test_oidc_key_pair_initialized(self):
        assert _main._oidc_key_pair is not None

    def test_oidc_policy_loaded(self):
        assert _main._OIDC_POLICY.get("issuer")
        assert _main._OIDC_POLICY.get("audience")

    def test_oidc_jwks_endpoint(self, client):
        r = client.get("/oidc/jwks")
        assert r.status_code == 200
        body = r.json()
        assert "keys" in body
        assert len(body["keys"]) == 1
        assert body["keys"][0]["alg"] == "RS256"

    def test_health_shows_oidc_enabled(self, client):
        body = client.get("/health").json()
        assert body.get("hitl_oidc_path") == "ENABLED"


class TestOIDCApproval:
    def test_oidc_token_approve_returns_200(self, client):
        tid, event_id = _start_and_get_event_id(client)
        token = _make_oidc_token(_HITL_APPROVER, event_id)
        r = client.post("/approve",
                        json={"thread_id": tid, "decision": "approve",
                              "hitl_token": token, "hitl_approver_id": _HITL_APPROVER},
                        headers={"X-API-Key": APPROVER_KEY})
        assert r.status_code == 200

    def test_hmac_token_still_works(self, client):
        tid, event_id = _start_and_get_event_id(client)
        token = _make_hmac_token(_HITL_APPROVER, event_id)
        r = client.post("/approve",
                        json={"thread_id": tid, "decision": "approve",
                              "hitl_token": token, "hitl_approver_id": _HITL_APPROVER},
                        headers={"X-API-Key": APPROVER_KEY})
        assert r.status_code == 200

    def test_oidc_wrong_approver_sub_returns_403(self, client):
        tid, event_id = _start_and_get_event_id(client)
        # Token sub = "approver-001" but approver_id = "wrong-approver"
        token = _make_oidc_token(_HITL_APPROVER, event_id)
        r = client.post("/approve",
                        json={"thread_id": tid, "decision": "approve",
                              "hitl_token": token, "hitl_approver_id": "wrong-approver"},
                        headers={"X-API-Key": APPROVER_KEY})
        assert r.status_code == 403

    def test_oidc_wrong_event_id_returns_403(self, client):
        tid, event_id = _start_and_get_event_id(client)
        token = _make_oidc_token(_HITL_APPROVER, "wrong-event-id-xyz")
        r = client.post("/approve",
                        json={"thread_id": tid, "decision": "approve",
                              "hitl_token": token, "hitl_approver_id": _HITL_APPROVER},
                        headers={"X-API-Key": APPROVER_KEY})
        assert r.status_code == 403

    def test_oidc_token_replay_returns_409(self, client):
        tid, event_id = _start_and_get_event_id(client)
        token = _make_oidc_token(_HITL_APPROVER, event_id)
        _main._mark_token_used(token, event_id, _HITL_APPROVER, _main.db_adapter)
        r = client.post("/approve",
                        json={"thread_id": tid, "decision": "approve",
                              "hitl_token": token, "hitl_approver_id": _HITL_APPROVER},
                        headers={"X-API-Key": APPROVER_KEY})
        assert r.status_code == 409

    def test_oidc_unregistered_sub_returns_403(self, client):
        tid, event_id = _start_and_get_event_id(client)
        # Generate token for approver not in registry
        token = _make_oidc_token("unregistered-attacker", event_id)
        r = client.post("/approve",
                        json={"thread_id": tid, "decision": "approve",
                              "hitl_token": token, "hitl_approver_id": "unregistered-attacker"},
                        headers={"X-API-Key": APPROVER_KEY})
        assert r.status_code == 403
