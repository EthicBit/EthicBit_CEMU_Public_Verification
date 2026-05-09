#!/usr/bin/env python3
"""
hitl_token_generator.py — generates HMAC-SHA256 HITL identity tokens for CI / testing.

Token format:
  HMAC-SHA256(shared_secret, approver_id + ":" + event_id + ":" + timestamp_floor_minutes)

The token is returned as a lowercase hex string.

Usage:
  python3 hitl_token_generator.py --approver approver-001 --event evt-abc123
  python3 hitl_token_generator.py --approver approver-001 --event evt-abc123 --secret mysecret
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import math
import os
import sys
import time


_DEFAULT_SECRET_ENV = "ETHICBIT_HITL_SHARED_SECRET"
_DEFAULT_SECRET_DEMO = "ethicbit-hitl-demo-secret-v1.4"


def generate_token(
    approver_id: str,
    event_id: str,
    shared_secret: str,
    timestamp: float | None = None,
) -> tuple[str, int]:
    """Return (hex_token, timestamp_floor_minutes)."""
    ts = timestamp if timestamp is not None else time.time()
    ts_floor = math.floor(ts / 60)
    payload = f"{approver_id}:{event_id}:{ts_floor}".encode()
    token = hmac.new(shared_secret.encode(), payload, hashlib.sha256).hexdigest()
    return token, ts_floor


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate HITL HMAC identity token")
    parser.add_argument("--approver", required=True, help="Approver ID")
    parser.add_argument("--event", required=True, help="Event ID")
    parser.add_argument("--secret", default=None, help="Shared secret (overrides env var)")
    args = parser.parse_args(argv)

    secret = (
        args.secret
        or os.environ.get(_DEFAULT_SECRET_ENV)
        or _DEFAULT_SECRET_DEMO
    )

    token, ts_floor = generate_token(args.approver, args.event, secret)
    print(f"approver_id:       {args.approver}")
    print(f"event_id:          {args.event}")
    print(f"timestamp_floor:   {ts_floor}")
    print(f"token:             {token}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
