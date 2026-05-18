#!/usr/bin/env python3
"""Pre-commit hook: block live AWS infrastructure IDs in public-facing files.

Detects patterns that look like real AWS resource IDs that should never
appear in committed files. Use sanitized identifiers instead.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Files that are explicitly allowed to contain sanitized references
ALLOWLISTED_PATHS = {
    "scripts/hooks/check_no_aws_ids.py",
    "memory/feedback_mirror_sync_and_infra_ids.md",
}

# Patterns for sensitive AWS infrastructure identifiers
PATTERNS = [
    (r"\brds\.amazonaws\.com\b", "RDS endpoint"),
    (r"\bi-[0-9a-f]{8,17}\b", "EC2 instance ID"),
    (r"\b[0-9]{12}\.dkr\.ecr\.", "ECR registry URL"),
    (r"cognito-idp\.[a-z0-9-]+\.amazonaws\.com", "Cognito IDP endpoint"),
]

# KMS key IDs (UUID format) are allowed only in scripts/crypto/ and assurance/
# Elsewhere they should use alias names only
KMS_KEY_ID_PATTERN = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"
)
KMS_ALLOWED_DIRS = {"scripts/crypto", "assurance/in-toto", "assurance/sbom", "memory"}


def check_file(path_str: str) -> list[str]:
    path = Path(path_str)
    rel = str(path)

    if any(rel.endswith(a) or rel == a for a in ALLOWLISTED_PATHS):
        return []

    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except (OSError, IsADirectoryError):
        return []

    violations: list[str] = []

    for pattern, label in PATTERNS:
        if re.search(pattern, content):
            violations.append(f"{rel}: contains {label} — use 'sanitized identifier' instead")

    # KMS key IDs only allowed in designated paths
    if KMS_KEY_ID_PATTERN.search(content):
        allowed = any(rel.startswith(d) for d in KMS_ALLOWED_DIRS)
        if not allowed:
            violations.append(
                f"{rel}: may contain a KMS key UUID — use alias name (e.g. alias/ethicbit-intoto-signing) in public-facing files"
            )

    return violations


def main() -> int:
    files = sys.argv[1:]
    all_violations: list[str] = []
    for f in files:
        all_violations.extend(check_file(f))

    if all_violations:
        print("AWS ID sanitization check FAILED:")
        for v in all_violations:
            print(f"  {v}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
