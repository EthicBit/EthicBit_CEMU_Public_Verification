#!/usr/bin/env python3
"""RFC 8785-style JSON canonicalization (SSOT helper).

This implementation is fail-closed for unsupported JSON types and non-finite numbers.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def _canonicalize(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"

    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)

    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise ValueError("non-finite float is not allowed by RFC 8785")
        if value == 0.0:
            return "0"
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)

    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)

    if isinstance(value, list):
        return "[" + ",".join(_canonicalize(item) for item in value) + "]"

    if isinstance(value, dict):
        keys = list(value.keys())
        if not all(isinstance(k, str) for k in keys):
            raise ValueError("JSON object keys must be strings")
        keys.sort()
        pairs: list[str] = []
        for key in keys:
            key_json = json.dumps(key, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
            val_json = _canonicalize(value[key])
            pairs.append(f"{key_json}:{val_json}")
        return "{" + ",".join(pairs) + "}"

    raise ValueError(f"unsupported JSON type for canonicalization: {type(value).__name__}")


def canonicalize_text(value: Any) -> str:
    return _canonicalize(value)


def canonicalize_bytes(value: Any) -> bytes:
    return canonicalize_text(value).encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Canonicalize JSON using RFC 8785-style ordering")
    parser.add_argument("input", help="Input JSON file")
    parser.add_argument("--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    in_path = Path(args.input)
    payload = json.loads(in_path.read_text(encoding="utf-8"))
    canonical = canonicalize_text(payload)

    if args.output:
        Path(args.output).write_text(canonical, encoding="utf-8")
    else:
        print(canonical)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
