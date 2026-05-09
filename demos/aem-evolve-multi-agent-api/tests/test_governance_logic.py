"""
Unit tests for core governance logic: SHA-256 hashing, gate outcomes, audit chain.
"""
import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import main as _main
from main import (
    compute_sha256,
    create_evolution_event,
    evaluate_evolution_gate,
    init_audit_tables,
    _append_audit_chain,
    _verify_artifact_signature,
    _is_token_used,
    _mark_token_used,
    GENESIS_HASH,
)
from db_adapter import SQLiteAdapter


@pytest.fixture
def mem_db():
    adapter = SQLiteAdapter(":memory:")
    init_audit_tables(adapter)
    yield adapter
    adapter.close()


# ── compute_sha256 ─────────────────────────────────────────────────────────────

class TestComputeSha256:
    def test_deterministic(self):
        d = {"b": 2, "a": 1}
        assert compute_sha256(d) == compute_sha256(d)

    def test_key_order_irrelevant(self):
        d1 = {"a": 1, "b": 2}
        d2 = {"b": 2, "a": 1}
        assert compute_sha256(d1) == compute_sha256(d2)

    def test_known_value(self):
        d = {"x": 1}
        canonical = json.dumps(d, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        expected = hashlib.sha256(canonical.encode()).hexdigest()
        assert compute_sha256(d) == expected

    def test_different_data_different_hash(self):
        assert compute_sha256({"a": 1}) != compute_sha256({"a": 2})

    def test_returns_hex_string_64(self):
        h = compute_sha256({"k": "v"})
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


# ── evaluate_evolution_gate outcomes ──────────────────────────────────────────

class TestGateOutcomes:
    def _make_event(self, score):
        return {
            "event_id": f"EVO-TEST-{score}",
            "materiality_score": score,
            "requested_claim_scope": "RESEARCH_SUPPORT",
            "claim_boundary": {
                "research_support_only": True,
                "clinical_claimed": False,
                "diagnostic_claimed": False,
                "regulatory_approval_claimed": False,
                "third_party_binding": False,
            },
            "event_canonical_sha256": "abc123",
        }

    def test_pass_outcome(self, mem_db):
        event = self._make_event(50.0)
        receipt = evaluate_evolution_gate(event, mem_db, "t-pass")
        assert receipt["receipt_payload"]["outcome"] == "PASS"

    def test_pass_boundary(self, mem_db):
        event = self._make_event(70.0)
        receipt = evaluate_evolution_gate(event, mem_db, "t-pass-boundary")
        assert receipt["receipt_payload"]["outcome"] == "PASS"

    def test_scope_limited_outcome(self, mem_db):
        event = self._make_event(75.0)
        receipt = evaluate_evolution_gate(event, mem_db, "t-scope")
        assert receipt["receipt_payload"]["outcome"] == "SCOPE_LIMITED"

    def test_scope_limited_upper_boundary(self, mem_db):
        event = self._make_event(85.0)
        receipt = evaluate_evolution_gate(event, mem_db, "t-scope-upper")
        assert receipt["receipt_payload"]["outcome"] == "SCOPE_LIMITED"

    def test_fail_closed_outcome(self, mem_db):
        event = self._make_event(90.0)
        receipt = evaluate_evolution_gate(event, mem_db, "t-fail")
        assert receipt["receipt_payload"]["outcome"] == "FAIL_CLOSED"

    def test_receipt_has_canonical_sha256(self, mem_db):
        event = self._make_event(50.0)
        receipt = evaluate_evolution_gate(event, mem_db, "t-sha")
        assert "receipt_canonical_sha256" in receipt
        assert len(receipt["receipt_canonical_sha256"]) == 64

    def test_receipt_schema_id(self, mem_db):
        event = self._make_event(50.0)
        receipt = evaluate_evolution_gate(event, mem_db, "t-schema")
        assert receipt["schema_id"] == "AEM_EVOLVE_EVOLUTION_RECEIPT_SCHEMA_V1"

    def test_receipt_has_signature(self, mem_db):
        event = self._make_event(50.0)
        receipt = evaluate_evolution_gate(event, mem_db, "t-sig")
        assert "signature_hex" in receipt
        assert len(receipt["signature_hex"]) > 0
        assert receipt["signature_status"] != "NOT_SIGNED_DEMO"

    def test_receipt_persisted_in_db(self, mem_db):
        event = self._make_event(60.0)
        evaluate_evolution_gate(event, mem_db, "t-persist")
        rows = mem_db.execute(
            "SELECT outcome FROM evolution_receipts WHERE thread_id = 't-persist'"
        )
        assert rows and rows[0][0] == "PASS"


# ── create_evolution_event ─────────────────────────────────────────────────────

class TestCreateEvolutionEvent:
    def test_event_has_required_fields(self, mem_db):
        evt = create_evolution_event("CONFIG_UPDATE", "artifact", "new_state", 55.0, mem_db, "t-evt")
        for field in ("event_id", "event_canonical_sha256", "materiality_score", "claim_boundary"):
            assert field in evt

    def test_event_has_signature(self, mem_db):
        evt = create_evolution_event("CONFIG_UPDATE", "artifact", "state", 55.0, mem_db, "t-sig-evt")
        assert "signature_hex" in evt
        assert evt["signature_status"] != "NOT_SIGNED_DEMO"

    def test_event_persisted(self, mem_db):
        create_evolution_event("CONFIG_UPDATE", "artifact", "state", 55.0, mem_db, "t-evtdb")
        rows = mem_db.execute(
            "SELECT COUNT(*) FROM evolution_events WHERE thread_id = 't-evtdb'"
        )
        assert rows[0][0] == 1

    def test_event_sha_matches_recompute(self, mem_db):
        evt = create_evolution_event("CONFIG_UPDATE", "art", "st", 55.0, mem_db, "t-sha-evt")
        stored_sha = evt["event_canonical_sha256"]
        # SHA is computed before signature and sha fields are added; exclude them from recompute.
        _exclude = {"event_canonical_sha256", "signature_hex", "signature_algorithm", "signature_status"}
        evt_copy = {k: v for k, v in evt.items() if k not in _exclude}
        assert stored_sha == compute_sha256(evt_copy)

    def test_event_id_format(self, mem_db):
        evt = create_evolution_event("CONFIG_UPDATE", "art", "st", 55.0, mem_db, "t-id")
        assert evt["event_id"].startswith("EVO-API-")


# ── read-time signature verification ──────────────────────────────────────────

class TestReadTimeSignatureVerification:
    def _make_event(self, score):
        return {
            "event_id": f"EVO-TEST-{score}",
            "materiality_score": score,
            "requested_claim_scope": "RESEARCH_SUPPORT",
            "claim_boundary": {
                "research_support_only": True,
                "clinical_claimed": False,
                "diagnostic_claimed": False,
                "regulatory_approval_claimed": False,
                "third_party_binding": False,
            },
            "event_canonical_sha256": "abc123",
        }

    def test_event_signature_verified_at_read(self, mem_db):
        evt = create_evolution_event("CONFIG_UPDATE", "art", "st", 55.0, mem_db, "t-rv-evt")
        verified = _verify_artifact_signature(evt)
        assert verified["signature_verified"] is True
        assert verified["signature_verification_note"] == "verified_at_read_time"

    def test_receipt_signature_verified_at_read(self, mem_db):
        event = self._make_event(50.0)
        receipt = evaluate_evolution_gate(event, mem_db, "t-rv-rec")
        verified = _verify_artifact_signature(receipt)
        assert verified["signature_verified"] is True

    def test_tampered_sig_fails_verification(self, mem_db):
        evt = create_evolution_event("CONFIG_UPDATE", "art", "st", 55.0, mem_db, "t-rv-tamper")
        tampered = dict(evt)
        tampered["signature_hex"] = "00" * 64
        verified = _verify_artifact_signature(tampered)
        assert verified["signature_verified"] is False

    def test_missing_sig_fields_returns_false(self):
        artifact = {"event_canonical_sha256": "abc", "outcome": "PASS"}
        verified = _verify_artifact_signature(artifact)
        assert verified["signature_verified"] is False
        assert verified["signature_verification_note"] == "missing_signature_fields"

    def test_verification_note_present(self, mem_db):
        evt = create_evolution_event("CONFIG_UPDATE", "art", "st", 55.0, mem_db, "t-rv-note")
        verified = _verify_artifact_signature(evt)
        assert "signature_verification_note" in verified


# ── replay mitigation ──────────────────────────────────────────────────────────

class TestReplayMitigation:
    def test_token_not_used_initially(self, mem_db):
        assert not _is_token_used("some-token-hex", "evt-001", mem_db)

    def test_mark_then_is_used(self, mem_db):
        _mark_token_used("tok-abc", "evt-002", "approver-001", mem_db)
        assert _is_token_used("tok-abc", "evt-002", mem_db)

    def test_different_event_not_used(self, mem_db):
        _mark_token_used("tok-xyz", "evt-003", "approver-001", mem_db)
        assert not _is_token_used("tok-xyz", "evt-999", mem_db)

    def test_mark_idempotent(self, mem_db):
        _mark_token_used("tok-dup", "evt-004", "approver-001", mem_db)
        _mark_token_used("tok-dup", "evt-004", "approver-001", mem_db)
        assert _is_token_used("tok-dup", "evt-004", mem_db)


# ── audit chain ───────────────────────────────────────────────────────────────

class TestAuditChain:
    def test_genesis_uses_zero_prev(self, mem_db):
        _append_audit_chain(mem_db, "test_entry", "entry-1", "sha" * 10 + "abcd")
        rows = mem_db.execute(
            "SELECT prev_chain_hash FROM audit_chain WHERE entry_id = 'entry-1'"
        )
        assert rows[0][0] == GENESIS_HASH

    def test_chain_hash_computed_correctly(self, mem_db):
        entry_sha = "a" * 64
        _append_audit_chain(mem_db, "evt", "entry-chain-1", entry_sha)
        expected = hashlib.sha256(f"{GENESIS_HASH}:{entry_sha}".encode()).hexdigest()
        rows = mem_db.execute(
            "SELECT chain_hash FROM audit_chain WHERE entry_id = 'entry-chain-1'"
        )
        assert rows[0][0] == expected

    def test_second_entry_links_to_first(self, mem_db):
        _append_audit_chain(mem_db, "e1", "link-1", "x" * 64)
        rows1 = mem_db.execute(
            "SELECT chain_hash FROM audit_chain WHERE entry_id = 'link-1'"
        )
        first_chain_hash = rows1[0][0]

        _append_audit_chain(mem_db, "e2", "link-2", "y" * 64)
        rows2 = mem_db.execute(
            "SELECT prev_chain_hash FROM audit_chain WHERE entry_id = 'link-2'"
        )
        assert rows2[0][0] == first_chain_hash
