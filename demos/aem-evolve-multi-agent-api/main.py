"""
Technical Demonstration: Multi-Agent AEM-EVOLVE™ Governance API
FastAPI + LangGraph + SQLite + Explicit Audit Tables + RBAC + Structured Logging + Metrics
May 2026 — v2.0 PR 14: Governance sign-off gate
"""

import logging
import logging.config
import os
import sys

# ── Structured logging ────────────────────────────────────────────────────────
_LOG_LEVEL = os.environ.get("AEM_LOG_LEVEL", "INFO").upper()


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        import json as _json
        from datetime import datetime, timezone
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        extra_keys = {
            k: v for k, v in record.__dict__.items()
            if k not in logging.LogRecord.__dict__ and not k.startswith("_")
            and k not in ("msg", "args", "levelname", "levelno", "name",
                          "pathname", "filename", "module", "exc_info",
                          "exc_text", "stack_info", "lineno", "funcName",
                          "created", "msecs", "relativeCreated", "thread",
                          "threadName", "processName", "process", "message",
                          "taskName")
        }
        payload.update(extra_keys)
        return _json.dumps(payload, ensure_ascii=False)


logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"json": {"()": _JsonFormatter}},
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "json",
        }
    },
    "root": {"level": _LOG_LEVEL, "handlers": ["stdout"]},
})

log = logging.getLogger("aem_evolve_api")

# ── Signing provider — initialized at import time ─────────────────────────────
_SIGNING_KEY_FILE_NAME = "signing_key.pem"
_OIDC_KEY_FILE_NAME    = "oidc_key.pem"


def _init_signing_provider():
    """
    Priority:
      (0) v2.0 PR 2 — KMS/HSM production provider (AEM_KMS_PROVIDER set)
      (1) env var PEM
      (2) file-based persistent key
      (3) generate + persist
    """
    # (0) v2.0 PR 2 — production KMS/HSM path
    try:
        from signing.production_kms_provider import ProductionKmsProvider
        kms = ProductionKmsProvider.from_env()
        if kms is not None:
            log.info("kms_signing_provider_loaded", extra={
                "provider": kms.config.provider,
                "key_id": kms.config.key_id,
                "algorithm": kms.config.algorithm,
            })
            return kms, f"SIGNED_KMS_{kms.config.provider.upper()}"
    except Exception as exc:
        log.warning("kms_signing_provider_init_failed", extra={"exc": str(exc)})

    # (1) Env var — explicit secret wins
    try:
        from signing.env_signing_provider import EnvSigningProvider
        provider = EnvSigningProvider()
        log.info("signing_provider_loaded", extra={"provider": "EnvSigningProvider"})
        return provider, "SIGNED_Ed25519_ENV"
    except Exception:
        pass

    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization

    key_file = DEMO_ROOT / _SIGNING_KEY_FILE_NAME

    # (2) Persistent file key — reload across restarts
    try:
        from signing.file_signing_provider import FileSigningProvider
        provider = FileSigningProvider(key_file)
        log.info("signing_provider_loaded", extra={"provider": "FileSigningProvider", "key_file": str(key_file)})
        return provider, "SIGNED_Ed25519_FILE"
    except FileNotFoundError:
        pass  # file doesn't exist yet — generate and persist below

    # (3) Generate a new key and write it to the persistent file
    _key = Ed25519PrivateKey.generate()
    pem = _key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    key_file.write_bytes(pem)
    log.info("signing_key_generated", extra={"key_file": str(key_file)})

    from signing.file_signing_provider import FileSigningProvider
    provider = FileSigningProvider(key_file)
    log.info("signing_provider_loaded", extra={"provider": "FileSigningProvider(generated)", "key_file": str(key_file)})
    return provider, "SIGNED_Ed25519_FILE"


from fastapi import FastAPI, HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, field_validator
from typing import Literal, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
import time
from datetime import datetime, timezone
import hashlib
import json
from uuid import uuid4
import uvicorn
from pathlib import Path
from metrics import registry as _metrics
from db_adapter import DBAdapter, SQLiteAdapter

DEMO_ROOT = Path(__file__).resolve().parent

# ── Tool path for signing + hitl packages ────────────────────────────────────
_TOOLS_PATH = str(DEMO_ROOT / "tools")
if _TOOLS_PATH not in sys.path:
    sys.path.insert(0, _TOOLS_PATH)

app = FastAPI(
    title="EthicBit AEM-EVOLVE™ Technical Demonstration",
    description="Multi-Agent Governance with RBAC HITL Controls — v2.0 PR 1: Production OIDC provider enforcement layer",
    version="0.21.0-demo",
)


@app.middleware("http")
async def _log_requests(request: Request, call_next):
    t0 = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 3)
    _metrics._timings[f"http_{request.method.lower()}_{request.url.path.strip('/').replace('/', '_')}"].append(elapsed_ms)
    log.info(
        "request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": elapsed_ms,
        },
    )
    return response

# ============================================
# AUTH — ROLE-BASED API KEY
# ============================================

_AUTH_KEYS_PATH = DEMO_ROOT / "configs" / "auth_demo_keys.json"
_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Roles
ROLE_INITIATOR = "INITIATOR"
ROLE_APPROVER = "APPROVER"
ROLE_OBSERVER = "OBSERVER"
_ALL_ROLES = {ROLE_INITIATOR, ROLE_APPROVER, ROLE_OBSERVER}


def _load_key_store() -> dict[str, str]:
    """Return {api_key: role} mapping. Falls back to env var AEM_DEMO_AUTH_KEYS_JSON."""
    import os
    env_raw = os.environ.get("AEM_DEMO_AUTH_KEYS_JSON", "")
    if env_raw:
        try:
            data = json.loads(env_raw)
            return {k: v["role"] for k, v in data.get("keys", {}).items()}
        except Exception:
            pass
    if _AUTH_KEYS_PATH.exists():
        data = json.loads(_AUTH_KEYS_PATH.read_text(encoding="utf-8"))
        return {k: v["role"] for k, v in data.get("keys", {}).items()}
    return {}


_KEY_STORE: dict[str, str] = _load_key_store()


def _require_role(api_key: str | None, required_role: str) -> str:
    """Validate key and role. Returns the role string. Raises 401/403 on failure."""
    if not api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header required")
    role = _KEY_STORE.get(api_key)
    if role is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    if role != required_role:
        raise HTTPException(
            status_code=403,
            detail=f"Role {required_role} required; your key has role {role}",
        )
    return role


def _require_any_auth(api_key: str | None) -> str:
    """Validate key; any role allowed. Returns the role string."""
    if not api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header required")
    role = _KEY_STORE.get(api_key)
    if role is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return role


# ── Signing + HITL — module-level singletons ─────────────────────────────────
_signing_provider, _SIGNING_STATUS = _init_signing_provider()
# v2.0 PR 2 — expose KMS provider directly for gate_check() in /health
_production_kms_provider = (
    _signing_provider
    if _SIGNING_STATUS.startswith("SIGNED_KMS_")
    else None
)


def _load_hitl_policy() -> dict:
    policy_path = DEMO_ROOT / "tools" / "hitl" / "HITL_IDENTITY_POLICY.json"
    if policy_path.exists():
        return json.loads(policy_path.read_text(encoding="utf-8"))
    return {"token_ttl_minutes": 10, "approver_registry": []}


def _get_hitl_secret() -> str:
    return os.environ.get("ETHICBIT_HITL_SHARED_SECRET", "ethicbit-hitl-demo-secret-v1.4")


def _verify_hitl_token(token: str, approver_id: str, event_id: str) -> tuple[bool, str]:
    # Auto-detect format: JWT (3 dot-separated segments) → OIDC; hex string → HMAC
    if token.count(".") == 2:
        return _verify_hitl_token_oidc(token, approver_id, event_id)
    try:
        from hitl.hitl_identity_verifier import verify_token
        policy = _load_hitl_policy()
        secret = _get_hitl_secret()
        return verify_token(token, approver_id, event_id, secret, policy)
    except ImportError as exc:
        return False, f"HITL verifier unavailable: {exc}"


_hitl_policy: dict = _load_hitl_policy()

# ── OIDC provider — initialized after sys.path is set ────────────────────────
_oidc_key_pair: object | None = None
_OIDC_POLICY: dict = {}
# v2.0 PR 1 — production OIDC provider (external IdP; None when OIDC_ISSUER not set)
_production_oidc_provider: object | None = None


def _init_oidc_provider() -> None:
    global _oidc_key_pair, _OIDC_POLICY, _production_oidc_provider

    # ── v2.0 PR 1: Production path — external OIDC provider via env vars ──────
    try:
        _demo_root_str = str(DEMO_ROOT)
        if _demo_root_str not in sys.path:
            sys.path.insert(0, _demo_root_str)
        from security.oidc_provider import ProductionOidcProvider
        provider = ProductionOidcProvider.from_env()
        if provider is not None:
            _production_oidc_provider = provider
            log.info("production_oidc_provider_loaded", extra={
                "issuer": provider.config.issuer,
                "jwks_uri": provider.config.jwks_uri,
                "audience": provider.config.audience,
            })
    except Exception as exc:
        log.warning("production_oidc_provider_init_failed", extra={"exc": str(exc)})

    # ── Demo path — local RSA key pair (fallback) ─────────────────────────────
    policy_path = DEMO_ROOT / "tools" / "hitl" / "HITL_OIDC_POLICY.json"
    if not policy_path.exists():
        log.warning("oidc_policy_not_found", extra={"path": str(policy_path)})
        return
    try:
        _OIDC_POLICY = json.loads(policy_path.read_text(encoding="utf-8"))
        from hitl.oidc_token_generator import OidcTestKeyPair
        key_file = DEMO_ROOT / _OIDC_KEY_FILE_NAME
        _oidc_key_pair = OidcTestKeyPair.load_or_generate(key_file)
        log.info("oidc_demo_provider_loaded", extra={
            "issuer": _OIDC_POLICY.get("issuer"),
            "key_file": str(key_file),
            "kid": _oidc_key_pair.key_id,
        })
    except Exception as exc:
        log.warning("oidc_provider_unavailable", extra={"exc": str(exc)})


def _verify_hitl_token_oidc(token: str, approver_id: str, event_id: str) -> tuple[bool, str]:
    """Verify an OIDC RS256 JWT HITL token — production path first, then demo path."""
    # ── v2.0 PR 1: Production path (external IdP) ─────────────────────────────
    if _production_oidc_provider is not None:
        try:
            ok, reason, claims = _production_oidc_provider.verify_token(token)  # type: ignore[union-attr]
            if not ok:
                return False, f"OIDC(prod): {reason}"
            if claims.get("sub") != approver_id:
                return False, f"OIDC(prod) sub {claims.get('sub')!r} != approver_id {approver_id!r}"
            token_event_id = claims.get("event_id", "")
            if token_event_id and token_event_id != event_id:
                return False, f"OIDC(prod) event_id {token_event_id!r} != {event_id!r}"
            return True, f"OIDC(prod) verified sub={claims.get('sub')!r}"
        except Exception as exc:
            _metrics.increment("oidc_provider_outage")
            return False, f"OIDC(prod) verification error: {exc}"

    # ── Demo path — local RSA key pair ────────────────────────────────────────
    if _oidc_key_pair is None:
        return False, "OIDC provider not initialized"
    try:
        from hitl.oidc_hitl_identity_verifier import verify_oidc_token
        jwks = _oidc_key_pair.jwks()  # type: ignore[attr-defined]
        ok, reason, payload = verify_oidc_token(token, jwks, _OIDC_POLICY)
        if not ok:
            return False, f"OIDC: {reason}"
        if payload.get("sub") != approver_id:
            return False, f"OIDC sub {payload.get('sub')!r} != approver_id {approver_id!r}"
        token_event_id = payload.get("event_id", "")
        if token_event_id and token_event_id != event_id:
            return False, f"OIDC event_id {token_event_id!r} != {event_id!r}"
        return True, f"OIDC verified sub={payload.get('sub')!r}"
    except Exception as exc:
        return False, f"OIDC verification error: {exc}"


_init_oidc_provider()

# ============================================
# CREAR TABLAS DE AUDITORÍA
# ============================================


def init_audit_tables(adapter: DBAdapter) -> None:
    for sql in [
        """CREATE TABLE IF NOT EXISTS evolution_events (
            event_id TEXT PRIMARY KEY,
            thread_id TEXT,
            event_canonical_sha256 TEXT,
            change_type TEXT,
            base_artifact TEXT,
            proposed_state TEXT,
            materiality_score REAL,
            requested_claim_scope TEXT,
            timestamp_utc TEXT,
            claim_boundary TEXT,
            event_json TEXT
        )""",
        """CREATE TABLE IF NOT EXISTS evolution_receipts (
            receipt_canonical_sha256 TEXT PRIMARY KEY,
            thread_id TEXT,
            event_id TEXT,
            outcome TEXT,
            receipt_message TEXT,
            materiality_score REAL,
            claim_boundary TEXT,
            requested_claim_scope TEXT,
            signature_status TEXT,
            timestamp_utc TEXT,
            receipt_json TEXT
        )""",
        """CREATE TABLE IF NOT EXISTS human_decisions (
            id SERIAL PRIMARY KEY,
            thread_id TEXT,
            event_id TEXT,
            decision TEXT,
            approver_id TEXT,
            override_reason TEXT,
            timestamp_utc TEXT
        )""",
        # Hash-linked audit chain: chain_hash = SHA256(prev + ":" + entry_sha256)
        """CREATE TABLE IF NOT EXISTS audit_chain (
            seq SERIAL PRIMARY KEY,
            entry_type TEXT NOT NULL,
            entry_id TEXT NOT NULL,
            entry_sha256 TEXT NOT NULL,
            prev_chain_hash TEXT NOT NULL,
            chain_hash TEXT NOT NULL,
            timestamp_utc TEXT NOT NULL
        )""",
        # Nonce store: SHA256(token) keyed by (token_hash, event_id) — replay prevention
        """CREATE TABLE IF NOT EXISTS hitl_used_tokens (
            token_hash TEXT NOT NULL,
            event_id TEXT NOT NULL,
            approver_id TEXT NOT NULL,
            used_at TEXT NOT NULL,
            PRIMARY KEY (token_hash, event_id)
        )""",
    ]:
        adapter.execute_write(sql)
    adapter.commit()


GENESIS_HASH = "0" * 64


def _append_audit_chain(
    adapter: DBAdapter,
    entry_type: str,
    entry_id: str,
    entry_sha256: str,
) -> str:
    try:
        rows = adapter.execute("SELECT chain_hash FROM audit_chain ORDER BY seq DESC LIMIT 1")
        prev_chain_hash = rows[0][0] if rows else GENESIS_HASH
        chain_hash = hashlib.sha256(f"{prev_chain_hash}:{entry_sha256}".encode()).hexdigest()
        adapter.execute_write(
            """INSERT INTO audit_chain
               (entry_type, entry_id, entry_sha256, prev_chain_hash, chain_hash, timestamp_utc)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (entry_type, entry_id, entry_sha256, prev_chain_hash, chain_hash,
             datetime.now(timezone.utc).isoformat()),
        )
        adapter.commit()
    except Exception:
        _metrics.increment("database_unavailable")
        raise
    log.info("audit_chain_append", extra={"entry_type": entry_type, "entry_id": entry_id, "chain_hash": chain_hash})
    return chain_hash


# ============================================
# MODELOS
# ============================================


class StartRequest(BaseModel):
    thread_id: str
    initial_prompt: str = "Eres un asistente general."
    materiality_score: float = 78.0

    @field_validator("thread_id")
    @classmethod
    def _thread_id_safe(cls, v: str) -> str:
        if not v or len(v) > 128 or not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("thread_id must be 1-128 alphanumeric/dash/underscore chars")
        return v

    @field_validator("initial_prompt")
    @classmethod
    def _prompt_length(cls, v: str) -> str:
        if len(v) > 4096:
            raise ValueError("initial_prompt must be ≤ 4096 characters")
        return v

    @field_validator("materiality_score")
    @classmethod
    def _materiality_range(cls, v: float) -> float:
        if not (0.0 <= v <= 100.0):
            raise ValueError("materiality_score must be between 0.0 and 100.0 inclusive")
        return v


class ApproveRequest(BaseModel):
    thread_id: str
    decision: Literal["approve", "reject"]
    override_reason: Optional[str] = None
    hitl_token: Optional[str] = None
    hitl_approver_id: Optional[str] = None

    @field_validator("thread_id")
    @classmethod
    def _thread_id_safe(cls, v: str) -> str:
        if not v or len(v) > 128 or not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("thread_id must be 1-128 alphanumeric/dash/underscore chars")
        return v


class StatusResponse(BaseModel):
    thread_id: str
    status: str
    current_prompt: str
    last_receipt: Optional[dict]
    human_approval_needed: bool
    approved_changes_count: int


# ============================================
# FUNCIONES AUXILIARES
# ============================================


def compute_sha256(data: dict) -> str:
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


_SIG_FIELDS = {"signature_hex", "signature_algorithm", "signature_status", "signature_verified",
               "signature_verification_note"}


def _verify_artifact_signature(artifact: dict) -> dict:
    """Return artifact copy with signature_verified + signature_verification_note fields."""
    result = dict(artifact)
    sig_hex = artifact.get("signature_hex")

    # Receipts may include both event_canonical_sha256 and receipt_canonical_sha256.
    # Verify receipts against receipt_canonical_sha256 first; otherwise verify events
    # against event_canonical_sha256.
    if "receipt_canonical_sha256" in artifact:
        canonical_sha256 = artifact.get("receipt_canonical_sha256")
    elif "event_canonical_sha256" in artifact:
        canonical_sha256 = artifact.get("event_canonical_sha256")
    else:
        canonical_sha256 = None

    if not sig_hex or not canonical_sha256:
        result["signature_verified"] = False
        result["signature_verification_note"] = "missing_signature_fields"
        return result

    try:
        sig_bytes = bytes.fromhex(sig_hex)
        ok = _signing_provider.verify(canonical_sha256.encode(), sig_bytes)
        result["signature_verified"] = ok
        result["signature_verification_note"] = (
            "verified_at_read_time" if ok else "signature_invalid"
        )
        if not ok:
            _metrics.increment("signature_verification_failed")
    except Exception as exc:
        result["signature_verified"] = False
        result["signature_verification_note"] = f"verification_error:{exc}"

    return result


def _is_token_used(token: str, event_id: str, adapter: DBAdapter) -> bool:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    rows = adapter.execute(
        "SELECT 1 FROM hitl_used_tokens WHERE token_hash = ? AND event_id = ?",
        (token_hash, event_id),
    )
    return len(rows) > 0


def _mark_token_used(token: str, event_id: str, approver_id: str, adapter: DBAdapter) -> None:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    adapter.execute_write(
        "INSERT OR IGNORE INTO hitl_used_tokens (token_hash, event_id, approver_id, used_at) "
        "VALUES (?, ?, ?, ?)",
        (token_hash, event_id, approver_id, datetime.now(timezone.utc).isoformat()),
    )
    adapter.commit()


def create_evolution_event(
    change_type: str,
    base_artifact: str,
    proposed_state: str,
    materiality: float,
    adapter: DBAdapter,
    thread_id: str,
) -> dict:
    event = {
        "schema_id": "AEM_EVOLVE_EVOLUTION_EVENT_SCHEMA_V1",
        "event_id": f"EVO-API-{uuid4()}",
        "thread_id": thread_id,
        "change_type": change_type,
        "base_artifact": base_artifact,
        "proposed_state": proposed_state,
        "materiality_score": materiality,
        "requested_claim_scope": "RESEARCH_SUPPORT",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": {
            "research_support_only": True,
            "clinical_claimed": False,
            "diagnostic_claimed": False,
            "regulatory_approval_claimed": False,
            "third_party_binding": False,
        },
    }
    event["event_canonical_sha256"] = compute_sha256(event)
    # Sign the event canonical hash
    try:
        sig_hex = _signing_provider.sign(event["event_canonical_sha256"].encode()).hex()
    except Exception:
        _metrics.increment("kms_signing_failed")
        raise
    event["signature_hex"] = sig_hex
    event["signature_algorithm"] = _signing_provider.algorithm()
    event["signature_status"] = _SIGNING_STATUS

    adapter.execute_write(
        """INSERT OR REPLACE INTO evolution_events
           (event_id, thread_id, event_canonical_sha256, change_type, base_artifact,
            proposed_state, materiality_score, requested_claim_scope, timestamp_utc,
            claim_boundary, event_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            event["event_id"], event["thread_id"], event["event_canonical_sha256"],
            event["change_type"], event["base_artifact"], event["proposed_state"],
            event["materiality_score"], event["requested_claim_scope"],
            event["timestamp_utc"], json.dumps(event["claim_boundary"], ensure_ascii=False),
            json.dumps(event, ensure_ascii=False),
        ),
    )
    adapter.commit()
    _append_audit_chain(adapter, "evolution_event", event["event_id"], event["event_canonical_sha256"])
    _metrics.increment("events_created")
    return event


def evaluate_evolution_gate(event: dict, adapter: DBAdapter, thread_id: str) -> dict:
    score = event["materiality_score"]

    if score > 85:
        outcome = "FAIL_CLOSED"
        message = "Cambio de muy alto riesgo. Requiere nueva evidencia o override excepcional."
    elif score > 70:
        outcome = "SCOPE_LIMITED"
        message = "Cambio aprobado con limitaciones de scope."
    else:
        outcome = "PASS"
        message = "Cambio de bajo riesgo. Aprobado automáticamente."

    receipt = {
        "schema_id": "AEM_EVOLVE_EVOLUTION_RECEIPT_SCHEMA_V1",
        "receipt_id": f"REC-{event['event_id']}",
        "receipt_payload": {
            "outcome": outcome,
            "receipt_message": message,
            "materiality_score": score,
            "claim_boundary": event["claim_boundary"],
            "requested_claim_scope": event["requested_claim_scope"],
        },
        "event_id": event["event_id"],
        "thread_id": thread_id,
        "event_canonical_sha256": event["event_canonical_sha256"],
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    receipt["receipt_canonical_sha256"] = compute_sha256(receipt)
    # Sign the receipt canonical hash
    try:
        sig_hex = _signing_provider.sign(receipt["receipt_canonical_sha256"].encode()).hex()
    except Exception:
        _metrics.increment("kms_signing_failed")
        raise
    receipt["signature_hex"] = sig_hex
    receipt["signature_algorithm"] = _signing_provider.algorithm()
    receipt["signature_status"] = _SIGNING_STATUS

    adapter.execute_write(
        """INSERT OR REPLACE INTO evolution_receipts
           (receipt_canonical_sha256, thread_id, event_id, outcome, receipt_message,
            materiality_score, claim_boundary, requested_claim_scope, signature_status,
            timestamp_utc, receipt_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            receipt["receipt_canonical_sha256"], receipt["thread_id"], receipt["event_id"],
            outcome, message, score, json.dumps(event["claim_boundary"], ensure_ascii=False),
            event["requested_claim_scope"], _SIGNING_STATUS, receipt["timestamp_utc"],
            json.dumps(receipt, ensure_ascii=False),
        ),
    )
    adapter.commit()
    _append_audit_chain(adapter, "evolution_receipt", receipt["receipt_id"], receipt["receipt_canonical_sha256"])
    _metrics.increment("receipts_issued")
    _metrics.increment(f"outcome_{outcome.lower()}")
    return receipt


# ============================================
# NODOS DEL GRAFO
# ============================================


def research_agent(state):
    state["research_findings"] = "Investigación completada."
    state["status"] = "research_completed"
    return state


def writer_agent(state, adapter):
    new_prompt = "Eres un escritor experto en ética de IA y gobernanza verificable."
    thread_id = state.get("thread_id", "unknown")
    materiality = float(state.get("materiality_score", 78.0))
    event = create_evolution_event(
        "CONFIGURATION_UPDATE", "writer_prompt", new_prompt, materiality, adapter, thread_id
    )
    receipt = evaluate_evolution_gate(event, adapter, thread_id)

    state["last_receipt"] = receipt
    state["pending_change"] = {"new_value": new_prompt, "event": event}
    state["status"] = "change_proposed"
    return state


def governance_gate(state):
    outcome = state["last_receipt"]["receipt_payload"]["outcome"]

    if outcome == "FAIL_CLOSED":
        state["status"] = "change_fail_closed"
        state["pending_change"] = None
        state["human_approval_needed"] = False
    elif outcome == "SCOPE_LIMITED":
        state["human_approval_needed"] = True
        state["status"] = "awaiting_human_approval"
    else:
        state["current_prompt"] = state["pending_change"]["new_value"]
        state["approved_changes"].append(state["last_receipt"])
        state["status"] = "change_auto_approved"
        state["pending_change"] = None
    return state


def awaiting_approval_node(state):
    state["status"] = "awaiting_human_approval"
    return state


def final_report_node(state):
    terminal_status = state["status"]
    state["final_report"] = f"Reporte completado. Estado final: {terminal_status}"
    state["terminal_status"] = terminal_status

    if terminal_status == "change_fail_closed":
        state["status"] = "completed_fail_closed"
    elif terminal_status == "change_human_rejected":
        state["status"] = "completed_rejected"
    else:
        state["status"] = "completed"
    return state


# ============================================
# GRAFO (con wrapper)
# ============================================


DEMO_DB_PATH = DEMO_ROOT / "ethicbit_demo.db"
DEMO_HOST = "127.0.0.1"
DEMO_PORT = 8000


def _build_db_adapter() -> tuple[DBAdapter, str]:
    """Instantiate the audit adapter from AEM_DB_ADAPTER / AEM_DB_URL env vars."""
    adapter_type = os.environ.get("AEM_DB_ADAPTER", "sqlite").lower()
    db_url = os.environ.get("AEM_DB_URL", "")
    if adapter_type == "postgres" and db_url:
        try:
            from db_adapter import PostgresAdapter
            adapter = PostgresAdapter(db_url)
            log.info("db_adapter_loaded", extra={"adapter": "PostgresAdapter", "url": db_url[:40]})
            return adapter, "PostgresAdapter"
        except Exception as exc:
            log.warning("postgres_adapter_failed_fallback_sqlite",
                        extra={"exc": str(exc)[:120]})
    return SQLiteAdapter(DEMO_DB_PATH), "SQLiteAdapter"


def build_graph():
    # Separate connections: LangGraph checkpointer gets its own conn to avoid
    # threading conflicts when SqliteSaver writes concurrently with audit inserts.
    import sqlite3 as _sqlite3
    _checkpoint_conn = _sqlite3.connect(str(DEMO_DB_PATH), check_same_thread=False)
    db_adapter, adapter_label = _build_db_adapter()
    init_audit_tables(db_adapter)

    def writer_agent_with_adapter(state):
        return writer_agent(state, db_adapter)

    workflow = StateGraph(dict)
    workflow.add_node("research", research_agent)
    workflow.add_node("writer", writer_agent_with_adapter)
    workflow.add_node("governance", governance_gate)
    workflow.add_node("awaiting_approval", awaiting_approval_node)
    workflow.add_node("final_report", final_report_node)

    workflow.set_entry_point("research")
    workflow.add_edge("research", "writer")
    workflow.add_edge("writer", "governance")

    def route(state):
        if state["status"] == "change_fail_closed":
            return "final_report"
        if state.get("human_approval_needed"):
            return "awaiting_approval"
        return "final_report"

    workflow.add_conditional_edges(
        "governance", route,
        {"awaiting_approval": "awaiting_approval", "final_report": "final_report"},
    )

    workflow.add_edge("awaiting_approval", END)
    workflow.add_edge("final_report", END)

    return workflow.compile(checkpointer=SqliteSaver(_checkpoint_conn)), db_adapter, adapter_label


graph, db_adapter, _db_adapter_label = build_graph()

# ── v2.0 PR 3 — PostgreSQL production persistence gate ───────────────────────
_postgres_persistence_gate: object | None = None
try:
    from db.postgres_production_gate import PostgresProductionGate
    _postgres_persistence_gate = PostgresProductionGate.from_env()
    if _postgres_persistence_gate is not None:
        log.info("postgres_production_gate_loaded", extra={"db_url_prefix": os.getenv("AEM_DB_URL", "")[:30]})
except Exception as _pg_gate_exc:
    log.warning("postgres_production_gate_init_failed", extra={"exc": str(_pg_gate_exc)})

# ── v2.0 PR 5 — Monitoring and alerting gate ──────────────────────────────────
try:
    from monitoring.monitoring_gate import MonitoringGate as _MonitoringGate
    _monitoring_gate = _MonitoringGate.from_env()
    log.info("monitoring_gate_loaded", extra={
        "prometheus_url_configured": _monitoring_gate._prometheus_url is not None,
    })
except Exception as _mon_gate_exc:
    _monitoring_gate = None
    log.warning("monitoring_gate_init_failed", extra={"exc": str(_mon_gate_exc)})

# ── v2.0 PR 6 — Incident response gate ───────────────────────────────────────
try:
    from incident_response.incident_response_gate import IncidentResponseGate as _IRGate
    _incident_response_gate = _IRGate.from_env()
    log.info("incident_response_gate_loaded", extra={
        "drill_completed": _incident_response_gate._drill_completed_at is not None,
    })
except Exception as _ir_gate_exc:
    _incident_response_gate = None
    log.warning("incident_response_gate_init_failed", extra={"exc": str(_ir_gate_exc)})

# ── v2.0 PR 7 — Security review gate ─────────────────────────────────────────
try:
    from security_review.security_review_gate import SecurityReviewGate as _SRGate
    _security_review_gate = _SRGate.from_env()
    log.info("security_review_gate_loaded", extra={
        "reviewer_set": _security_review_gate._security_reviewer is not None,
    })
except Exception as _sr_gate_exc:
    _security_review_gate = None
    log.warning("security_review_gate_init_failed", extra={"exc": str(_sr_gate_exc)})

# ── v2.0 PR 8 — Reproduction gate ────────────────────────────────────────────
try:
    from reproduction.reproduction_gate import ReproductionGate as _RepGate
    _reproduction_gate = _RepGate.from_env()
    log.info("reproduction_gate_loaded", extra={
        "reproducer_set": _reproduction_gate._reproducer_id is not None,
    })
except Exception as _rep_gate_exc:
    _reproduction_gate = None
    log.warning("reproduction_gate_init_failed", extra={"exc": str(_rep_gate_exc)})

# ── v2.0 PR 9 — Deployment audit gate ────────────────────────────────────────
try:
    from deployment.deployment_gate import DeploymentGate as _DeployGate
    _deployment_gate = _DeployGate.from_env()
    log.info("deployment_gate_loaded", extra={
        "target_set": _deployment_gate._deployment_target is not None,
    })
except Exception as _deploy_gate_exc:
    _deployment_gate = None
    log.warning("deployment_gate_init_failed", extra={"exc": str(_deploy_gate_exc)})

# ── v2.0 PR 10 — SLO evidence gate ───────────────────────────────────────────
try:
    from slo.slo_gate import SLOGate as _SLOGate
    _slo_gate = _SLOGate.from_env()
    log.info("slo_gate_loaded", extra={
        "reviewer_set": _slo_gate._slo_reviewer is not None,
    })
except Exception as _slo_gate_exc:
    _slo_gate = None
    log.warning("slo_gate_init_failed", extra={"exc": str(_slo_gate_exc)})

# ── v2.0 PR 11 — Rollback procedure gate ─────────────────────────────────────
try:
    from rollback.rollback_gate import RollbackGate as _RollbackGate
    _rollback_gate = _RollbackGate.from_env()
    log.info("rollback_gate_loaded", extra={
        "tester_set": _rollback_gate._rollback_tester is not None,
    })
except Exception as _rollback_gate_exc:
    _rollback_gate = None
    log.warning("rollback_gate_init_failed", extra={"exc": str(_rollback_gate_exc)})

# ── v2.0 PR 12 — Disaster recovery gate ──────────────────────────────────────
try:
    from disaster_recovery.disaster_recovery_gate import DisasterRecoveryGate as _DRGate
    _disaster_recovery_gate = _DRGate.from_env()
    log.info("disaster_recovery_gate_loaded", extra={
        "tester_set": _disaster_recovery_gate._dr_tester is not None,
    })
except Exception as _dr_gate_exc:
    _disaster_recovery_gate = None
    log.warning("disaster_recovery_gate_init_failed", extra={"exc": str(_dr_gate_exc)})

# ── v2.0 PR 13 — Production readiness gate aggregator ────────────────────────
try:
    from readiness.readiness_gate import ReadinessGate as _ReadinessGate
    _readiness_gate = _ReadinessGate.from_env()
    log.info("readiness_gate_loaded", extra={
        "reviewer_set": _readiness_gate._readiness_reviewer is not None,
    })
except Exception as _readiness_gate_exc:
    _readiness_gate = None
    log.warning("readiness_gate_init_failed", extra={"exc": str(_readiness_gate_exc)})

# ── v2.0 PR 14 — Governance sign-off gate ────────────────────────────────────
try:
    from governance_signoff.governance_signoff_gate import GovernanceSignoffGate as _GovernanceSignoffGate
    _governance_signoff_gate = _GovernanceSignoffGate.from_env()
    log.info("governance_signoff_gate_loaded", extra={
        "approver_set": _governance_signoff_gate._governance_approver is not None,
    })
except Exception as _governance_signoff_gate_exc:
    _governance_signoff_gate = None
    log.warning("governance_signoff_gate_init_failed", extra={"exc": str(_governance_signoff_gate_exc)})

# ============================================
# ENDPOINTS
# ============================================


@app.get("/oidc/jwks")
def get_oidc_jwks():
    """Return the server-side OIDC JWKS for demo token verification."""
    if _oidc_key_pair is None:
        raise HTTPException(503, "OIDC provider not available")
    return _oidc_key_pair.jwks()  # type: ignore[attr-defined]


@app.get("/healthz")
def healthz():
    try:
        db_adapter.execute("SELECT 1")
        db_ok = True
    except Exception:
        db_ok = False
    db_label = "postgres" if "Postgres" in _db_adapter_label else "sqlite"
    status = "ok" if db_ok else "degraded"
    return {"status": status, "db": db_label if db_ok else "unreachable", "version": "0.21.0-demo",
            "signing_status": _SIGNING_STATUS}


@app.get("/metrics")
def get_metrics(api_key: str = Security(_API_KEY_HEADER)):
    _require_any_auth(api_key)
    return _metrics.snapshot()


@app.post("/start")
def start_session(req: StartRequest, api_key: str = Security(_API_KEY_HEADER)):
    _require_role(api_key, ROLE_INITIATOR)
    initial_state = {
        "thread_id": req.thread_id,
        "research_findings": "",
        "final_report": "",
        "current_prompt": req.initial_prompt,
        "materiality_score": req.materiality_score,
        "pending_change": None,
        "last_receipt": None,
        "status": "initialized",
        "approved_changes": [],
        "human_approval_needed": False,
    }
    config = {"configurable": {"thread_id": req.thread_id}}
    with _metrics.timer("end_to_end"):
        result = graph.invoke(initial_state, config=config)
    _metrics.increment("sessions_started")
    return {"thread_id": req.thread_id, "status": result["status"]}


@app.get("/status/{thread_id}", response_model=StatusResponse)
def get_status(thread_id: str, api_key: str = Security(_API_KEY_HEADER)):
    _require_any_auth(api_key)
    config = {"configurable": {"thread_id": thread_id}}
    try:
        state = graph.get_state(config).values
        return StatusResponse(
            thread_id=thread_id,
            status=state.get("status", "unknown"),
            current_prompt=state.get("current_prompt", ""),
            last_receipt=state.get("last_receipt"),
            human_approval_needed=state.get("human_approval_needed", False),
            approved_changes_count=len(state.get("approved_changes", [])),
        )
    except Exception as e:
        raise HTTPException(404, f"Thread not found or unavailable: {str(e)}")


@app.post("/approve")
def approve_change(req: ApproveRequest, api_key: str = Security(_API_KEY_HEADER)):
    role = _require_role(api_key, ROLE_APPROVER)
    config = {"configurable": {"thread_id": req.thread_id}}
    state = graph.get_state(config).values

    if not state.get("human_approval_needed"):
        raise HTTPException(400, "No human approval needed")

    # ── HITL identity enforcement — mandatory for SCOPE_LIMITED outcomes ──────
    event_id = state["last_receipt"]["event_id"]
    if not req.hitl_token or not req.hitl_approver_id:
        raise HTTPException(
            400,
            "hitl_token and hitl_approver_id are required for SCOPE_LIMITED approvals. "
            "Generate a token with: tools/hitl/hitl_token_generator.py"
        )
    ok, reason = _verify_hitl_token(req.hitl_token, req.hitl_approver_id, event_id)
    if not ok:
        _metrics.increment("hitl_approval_failed")
        raise HTTPException(403, f"HITL token invalid: {reason}")

    # ── Replay mitigation — one-time use per (token, event_id) pair ──────────
    if _is_token_used(req.hitl_token, event_id, db_adapter):
        _metrics.increment("replay_attempt_detected")
        raise HTTPException(409, "HITL token already used (replay detected). Generate a new token.")
    _mark_token_used(req.hitl_token, event_id, req.hitl_approver_id, db_adapter)
    # ─────────────────────────────────────────────────────────────────────────

    approver_id = req.hitl_approver_id
    log.info("hitl_identity_verified", extra={"approver_id": approver_id, "event_id": event_id, "reason": reason})
    # ─────────────────────────────────────────────────────────────────────────

    if req.decision == "approve":
        state["current_prompt"] = state["pending_change"]["new_value"]
        state["approved_changes"].append(state["last_receipt"])
        state["status"] = "change_human_approved"
    else:
        state["status"] = "change_human_rejected"

    state["pending_change"] = None
    state["human_approval_needed"] = False

    decision_ts = datetime.now(timezone.utc).isoformat()
    decision_id = f"DEC-{req.thread_id}-{event_id}"
    decision_payload = {
        "decision_id": decision_id,
        "thread_id": req.thread_id,
        "event_id": event_id,
        "decision": req.decision,
        "approver_id": approver_id,
        "approver_role": role,
        "override_reason": req.override_reason,
        "timestamp_utc": decision_ts,
    }
    decision_sha256 = compute_sha256(decision_payload)

    db_adapter.execute_write(
        """INSERT INTO human_decisions
           (thread_id, event_id, decision, approver_id, override_reason, timestamp_utc)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (req.thread_id, event_id, req.decision, approver_id, req.override_reason, decision_ts),
    )
    db_adapter.commit()
    _append_audit_chain(db_adapter, "human_decision", decision_id, decision_sha256)
    log.info("human_decision_recorded", extra={"decision_id": decision_id, "decision": req.decision, "approver_id": approver_id})

    state = final_report_node(state)
    graph.update_state(config, state)
    return {"status": state["status"]}


@app.get("/receipt/{thread_id}")
def get_receipt(thread_id: str, api_key: str = Security(_API_KEY_HEADER)):
    _require_any_auth(api_key)
    config = {"configurable": {"thread_id": thread_id}}
    try:
        state = graph.get_state(config).values
        if not state.get("last_receipt"):
            raise HTTPException(404, "No receipt found")
        return _verify_artifact_signature(state["last_receipt"])
    except Exception as e:
        raise HTTPException(404, f"Thread not found or unavailable: {str(e)}")


@app.get("/event/{thread_id}")
def get_event(thread_id: str, api_key: str = Security(_API_KEY_HEADER)):
    _require_any_auth(api_key)
    rows = db_adapter.execute(
        "SELECT event_json FROM evolution_events WHERE thread_id = ? ORDER BY timestamp_utc DESC",
        (thread_id,),
    )
    events = [_verify_artifact_signature(json.loads(r[0])) for r in rows]
    return {"thread_id": thread_id, "events": events}


@app.get("/audit/{thread_id}")
def get_audit(thread_id: str, api_key: str = Security(_API_KEY_HEADER)):
    _require_any_auth(api_key)
    events = [_verify_artifact_signature(json.loads(r[0])) for r in db_adapter.execute(
        "SELECT event_json FROM evolution_events WHERE thread_id = ? ORDER BY timestamp_utc DESC",
        (thread_id,),
    )]
    receipts = [_verify_artifact_signature(json.loads(r[0])) for r in db_adapter.execute(
        "SELECT receipt_json FROM evolution_receipts WHERE thread_id = ? ORDER BY timestamp_utc DESC",
        (thread_id,),
    )]
    raw_decisions = db_adapter.execute(
        "SELECT event_id, decision, approver_id, override_reason, timestamp_utc "
        "FROM human_decisions WHERE thread_id = ? ORDER BY timestamp_utc DESC",
        (thread_id,),
    )
    decisions = [
        {"event_id": r[0], "decision": r[1], "approver_id": r[2],
         "override_reason": r[3], "timestamp_utc": r[4]}
        for r in raw_decisions
    ]
    return {"thread_id": thread_id, "events": events, "receipts": receipts, "human_decisions": decisions}


@app.get("/chain/verify")
def verify_chain(api_key: str = Security(_API_KEY_HEADER)):
    """Walk the full audit chain and verify every hash link."""
    _require_any_auth(api_key)
    rows = db_adapter.execute(
        "SELECT seq, entry_type, entry_id, entry_sha256, prev_chain_hash, chain_hash "
        "FROM audit_chain ORDER BY seq"
    )
    if not rows:
        return {"status": "EMPTY", "entries_checked": 0, "errors": []}

    errors = []
    expected_prev = GENESIS_HASH
    for seq, entry_type, entry_id, entry_sha256, prev_chain_hash, chain_hash in rows:
        if prev_chain_hash != expected_prev:
            errors.append({"seq": seq, "entry_id": entry_id,
                           "error": "prev_chain_hash_mismatch",
                           "expected": expected_prev, "got": prev_chain_hash})
        recomputed = hashlib.sha256(f"{prev_chain_hash}:{entry_sha256}".encode()).hexdigest()
        if recomputed != chain_hash:
            errors.append({"seq": seq, "entry_id": entry_id,
                           "error": "chain_hash_mismatch",
                           "expected": recomputed, "stored": chain_hash})
        expected_prev = chain_hash

    if errors:
        _metrics.increment("audit_chain_mismatch", len(errors))
    return {
        "status": "PASS" if not errors else "TAMPER_DETECTED",
        "entries_checked": len(rows),
        "errors": errors,
        "head_chain_hash": rows[-1][5] if rows else None,
        "tamper_evident": True,
        "tamper_proof_claimed": False,
        "note": "Hash-linked detection only. SQLite is demo storage — not tamper-proof.",
    }


@app.get("/chain/{thread_id}")
def get_chain(thread_id: str, api_key: str = Security(_API_KEY_HEADER)):
    """Return all audit chain entries for this thread."""
    _require_any_auth(api_key)
    event_ids = {r[0] for r in db_adapter.execute(
        "SELECT event_id FROM evolution_events WHERE thread_id = ?", (thread_id,))}
    receipt_ids = {f"REC-{r[0]}" for r in db_adapter.execute(
        "SELECT event_id FROM evolution_receipts WHERE thread_id = ?", (thread_id,))}
    decision_ids = {r[0] for r in db_adapter.execute(
        "SELECT entry_id FROM audit_chain WHERE entry_id LIKE ?", (f"DEC-{thread_id}-%",))}
    all_ids = event_ids | receipt_ids | decision_ids
    if not all_ids:
        raise HTTPException(404, f"No audit chain entries found for thread {thread_id}")
    placeholders = ",".join("?" * len(all_ids))
    rows = db_adapter.execute(
        f"SELECT seq, entry_type, entry_id, entry_sha256, prev_chain_hash, chain_hash, timestamp_utc "
        f"FROM audit_chain WHERE entry_id IN ({placeholders}) ORDER BY seq",
        tuple(all_ids),
    )
    entries = [
        {"seq": r[0], "entry_type": r[1], "entry_id": r[2],
         "entry_sha256": r[3], "prev_chain_hash": r[4],
         "chain_hash": r[5], "timestamp_utc": r[6]}
        for r in rows
    ]
    return {"thread_id": thread_id, "chain_entries": entries, "count": len(entries)}


@app.get("/health")
def health():
    roles_loaded = sorted(set(_KEY_STORE.values()))
    return {
        "status": "healthy",
        "demo_type": "technical_demonstration",
        "version": "0.21.0-demo",
        "local_only": True,
        "auth": {
            "scheme": "X-API-Key header",
            "roles_configured": roles_loaded,
            "hitl_role_required": ROLE_APPROVER,
            "initiation_role_required": ROLE_INITIATOR,
            "environment": "local-demo",
            "production_auth_claimed": False,
        },
        "signing_provider": _signing_provider.algorithm(),
        "signing_status": _SIGNING_STATUS,
        "kms_signing_gate": (
            _production_kms_provider.gate_check()  # type: ignore[union-attr]
            if _production_kms_provider is not None
            else {
                "gate": "HSM_KMS_SIGNING_CHECK",
                "status": "NOT_CONFIGURED",
                "reason": "AEM_KMS_PROVIDER env var not set",
                "non_exportable_posture": False,
            }
        ),
        "hitl_identity_enforcement": "HMAC_AND_OIDC_DUAL_PATH",
        "hitl_oidc_mode": "PRODUCTION" if _production_oidc_provider is not None else "DEMO",
        "hitl_oidc_path": "ENABLED" if (_oidc_key_pair is not None or _production_oidc_provider is not None) else "UNAVAILABLE",
        "production_oidc_gate": (
            _production_oidc_provider.gate_check()  # type: ignore[union-attr]
            if _production_oidc_provider is not None
            else {"gate": "PRODUCTION_OIDC_PROVIDER_CHECK", "status": "NOT_CONFIGURED", "reason": "OIDC_ISSUER env var not set"}
        ),
        "hitl_replay_mitigation": "ONE_TIME_USE_PER_TOKEN_EVENT_PAIR",
        "read_time_signature_verification": True,
        "key_persistence": "FILE_BASED" if "FILE" in _SIGNING_STATUS else "ENV_VAR",
        "oidc_key_persistence": "FILE_BASED" if (DEMO_ROOT / _OIDC_KEY_FILE_NAME).exists() else "EPHEMERAL",
        "materiality_parametrized": True,
        "governance_paths": ["FAIL_CLOSED", "SCOPE_LIMITED", "PASS"],
        "db_adapter": _db_adapter_label,
        "db_adapter_switch": "AEM_DB_ADAPTER env var (sqlite|postgres)",
        "migration_recovery_gate": {
            "gate": "MIGRATION_RECOVERY_CHECK",
            "rollback_files_present": len(list(
                (DEMO_ROOT / "migrations" / "rollback").glob("*.sql")
            )) if (DEMO_ROOT / "migrations" / "rollback").exists() else 0,
            "status": "CONFIGURED" if os.getenv("AEM_DB_URL") else "NOT_CONFIGURED",
            "note": "Run verify_migration_recovery.py for full gate check",
        },
        "monitoring_alerting_gate": (
            _monitoring_gate.gate_check()  # type: ignore[union-attr]
            if _monitoring_gate is not None
            else {
                "gate": "MONITORING_ALERTING_CHECK",
                "status": "NOT_CONFIGURED",
                "reason": "monitoring package unavailable",
            }
        ),
        "incident_response_gate": (
            _incident_response_gate.gate_check()  # type: ignore[union-attr]
            if _incident_response_gate is not None
            else {
                "gate": "INCIDENT_RESPONSE_CHECK",
                "status": "NOT_CONFIGURED",
                "reason": "incident_response package unavailable",
            }
        ),
        "security_review_gate": (
            _security_review_gate.gate_check()  # type: ignore[union-attr]
            if _security_review_gate is not None
            else {
                "gate": "SECURITY_REVIEW_CHECK",
                "status": "NOT_CONFIGURED",
                "reason": "security_review package unavailable",
            }
        ),
        "reproduction_gate": (
            _reproduction_gate.gate_check()  # type: ignore[union-attr]
            if _reproduction_gate is not None
            else {
                "gate": "EXTERNAL_REPRODUCTION_CHECK",
                "status": "NOT_CONFIGURED",
                "independent_reproduction_claimed": False,
                "reason": "reproduction package unavailable",
            }
        ),
        "deployment_gate": (
            _deployment_gate.gate_check()  # type: ignore[union-attr]
            if _deployment_gate is not None
            else {
                "gate": "PRODUCTION_DEPLOYMENT_AUDIT_CHECK",
                "status": "NOT_CONFIGURED",
                "production_deployed": False,
                "reason": "deployment package unavailable",
            }
        ),
        "slo_gate": (
            _slo_gate.gate_check()  # type: ignore[union-attr]
            if _slo_gate is not None
            else {
                "gate": "SLO_EVIDENCE_CHECK",
                "status": "NOT_CONFIGURED",
                "slo_evidence_verified": False,
                "reason": "slo package unavailable",
            }
        ),
        "rollback_gate": (
            _rollback_gate.gate_check()  # type: ignore[union-attr]
            if _rollback_gate is not None
            else {
                "gate": "ROLLBACK_PROCEDURE_CHECK",
                "status": "NOT_CONFIGURED",
                "rollback_tested": False,
                "reason": "rollback package unavailable",
            }
        ),
        "disaster_recovery_gate": (
            _disaster_recovery_gate.gate_check()  # type: ignore[union-attr]
            if _disaster_recovery_gate is not None
            else {
                "gate": "DISASTER_RECOVERY_CHECK",
                "status": "NOT_CONFIGURED",
                "dr_tested": False,
                "reason": "disaster_recovery package unavailable",
            }
        ),
        "readiness_gate": (
            _readiness_gate.gate_check()  # type: ignore[union-attr]
            if _readiness_gate is not None
            else {
                "gate": "PRODUCTION_READINESS_GATE",
                "status": "NOT_CONFIGURED",
                "production_ready": False,
                "gates_evidence_complete": False,
                "reason": "readiness package unavailable",
            }
        ),
        "governance_signoff_gate": (
            _governance_signoff_gate.gate_check()  # type: ignore[union-attr]
            if _governance_signoff_gate is not None
            else {
                "gate": "GOVERNANCE_SIGNOFF_CHECK",
                "status": "NOT_CONFIGURED",
                "governance_signed_off": False,
                "reason": "governance_signoff package unavailable",
            }
        ),
        "postgres_persistence_gate": (
            {"gate": "POSTGRES_PRODUCTION_PERSISTENCE_CHECK", "status": "NOT_CONFIGURED",
             "reason": "AEM_DB_URL env var not set"}
            if _postgres_persistence_gate is None
            else {
                "gate": "POSTGRES_PRODUCTION_PERSISTENCE_CHECK",
                "status": "CONFIGURED",
                "db_url_configured": True,
                "note": "Run verify_postgres_persistence.py for full gate check",
            }
        ),
        "audit_tables": ["evolution_events", "evolution_receipts", "human_decisions", "audit_chain", "hitl_used_tokens"],
        "tamper_evident_chain": True,
        "tamper_proof_claimed": False,
        "non_claims": [
            "not_production_ready",
            "not_independently_reproduced",
            "not_regulatory_approved",
            "not_clinical_or_diagnostic",
            "sqlite_not_production_audit_storage",
            "not_tamper_proof",
            "no_hsm_key_custody",
            "no_production_oidc_idp",
            "file_key_not_hsm_backed",
            "local_sqlite_replay_store_not_distributed",
        ],
    }


if __name__ == "__main__":
    print("Starting EthicBit AEM-EVOLVE Multi-Agent Governance API v0.21.0-demo")
    print(f"Docs: http://{DEMO_HOST}:{DEMO_PORT}/docs")
    uvicorn.run(app, host=DEMO_HOST, port=DEMO_PORT)
