"""
AEM-EVOLVE Multi-Agent Governance API — Python Client SDK

Minimal client for the AEM-EVOLVE demo API. Requires `requests`.

Usage:
    from aem_evolve_client import AEMEvolveClient

    client = AEMEvolveClient("http://127.0.0.1:8000", api_key="demo-initiator-key-001")
    result = client.start("my-session-001", "Initial prompt text")
    print(result)  # {"thread_id": "...", "status": "awaiting_human_approval"}

    approver = AEMEvolveClient("http://127.0.0.1:8000", api_key="demo-approver-key-001")
    approved = approver.approve("my-session-001", "approve", override_reason="Reviewed scope limits")
    print(approved)  # {"status": "completed"}
"""

from __future__ import annotations

from typing import Optional

try:
    import requests
except ImportError as e:
    raise ImportError("aem_evolve_client requires the 'requests' package: pip install requests") from e


class AEMEvolveError(Exception):
    """Raised when the API returns a non-2xx response."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")


class AEMEvolveClient:
    """HTTP client for the AEM-EVOLVE Multi-Agent Governance API.

    Args:
        base_url: Server base URL (e.g. ``"http://127.0.0.1:8000"``).
        api_key: ``X-API-Key`` header value. Role must match the operation:
            INITIATOR for ``start()``, APPROVER for ``approve()``, any for reads.
        timeout: Request timeout in seconds (default: 30).
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        api_key: str = "",
        timeout: float = 30.0,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._key = api_key
        self._timeout = timeout
        self._session = requests.Session()
        if api_key:
            self._session.headers["X-API-Key"] = api_key

    # ── private ──────────────────────────────────────────────────────────────

    def _get(self, path: str) -> dict:
        r = self._session.get(f"{self._base}{path}", timeout=self._timeout)
        return self._handle(r)

    def _post(self, path: str, payload: dict) -> dict:
        r = self._session.post(f"{self._base}{path}", json=payload, timeout=self._timeout)
        return self._handle(r)

    @staticmethod
    def _handle(response: "requests.Response") -> dict:
        if response.ok:
            return response.json()
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
        raise AEMEvolveError(response.status_code, detail)

    # ── public API ───────────────────────────────────────────────────────────

    def health(self) -> dict:
        """GET /health — no auth required."""
        return self._get("/health")

    def healthz(self) -> dict:
        """GET /healthz — DB liveness probe, no auth required."""
        return self._get("/healthz")

    def start(self, thread_id: str, initial_prompt: str = "Eres un asistente general.") -> dict:
        """POST /start — requires INITIATOR role.

        Returns:
            ``{"thread_id": ..., "status": "awaiting_human_approval"}``
        """
        return self._post("/start", {"thread_id": thread_id, "initial_prompt": initial_prompt})

    def approve(
        self,
        thread_id: str,
        decision: str,
        override_reason: Optional[str] = None,
    ) -> dict:
        """POST /approve — requires APPROVER role.

        Args:
            decision: ``"approve"`` or ``"reject"``.
            override_reason: Optional justification text.

        Returns:
            ``{"status": "completed"}`` or similar.
        """
        payload: dict = {"thread_id": thread_id, "decision": decision}
        if override_reason is not None:
            payload["override_reason"] = override_reason
        return self._post("/approve", payload)

    def status(self, thread_id: str) -> dict:
        """GET /status/{thread_id} — any role."""
        return self._get(f"/status/{thread_id}")

    def receipt(self, thread_id: str) -> dict:
        """GET /receipt/{thread_id} — any role. Returns the last Evolution Receipt."""
        return self._get(f"/receipt/{thread_id}")

    def event(self, thread_id: str) -> dict:
        """GET /event/{thread_id} — any role. Returns all Evolution Events."""
        return self._get(f"/event/{thread_id}")

    def audit(self, thread_id: str) -> dict:
        """GET /audit/{thread_id} — any role. Returns events, receipts, and decisions."""
        return self._get(f"/audit/{thread_id}")

    def chain(self, thread_id: str) -> dict:
        """GET /chain/{thread_id} — any role. Returns audit chain entries for the thread."""
        return self._get(f"/chain/{thread_id}")

    def verify_chain(self) -> dict:
        """GET /chain/verify — any role. Verifies integrity of the full audit chain."""
        return self._get("/chain/verify")

    def metrics(self) -> dict:
        """GET /metrics — any role. Returns in-memory performance metrics."""
        return self._get("/metrics")
