"""
Shared fixtures for AEM-EVOLVE test suite.
"""
import os
import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure the demo root is on sys.path.
DEMO_ROOT = Path(__file__).resolve().parent.parent
if str(DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEMO_ROOT))

os.environ.setdefault("AEM_LOG_LEVEL", "WARNING")

# Import app after path setup.
import main as _main  # noqa: E402

app = _main.app


@pytest.fixture(scope="session")
def client():
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ── Canonical auth keys (matching configs/auth_demo_keys.json) ─────────────────
INITIATOR_KEY = "demo-initiator-key-001"
APPROVER_KEY = "demo-approver-key-001"
OBSERVER_KEY = "demo-observer-key-001"
UNKNOWN_KEY = "not-a-real-key-xyz"


def unique_tid() -> str:
    """Return a unique, validator-safe thread_id."""
    return f"t-{uuid.uuid4().hex[:20]}"
