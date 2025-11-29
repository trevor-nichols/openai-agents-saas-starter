#!/usr/bin/env python3
"""CI helper for detecting placeholder secrets."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api-service"))

from app.core.config import Settings  # noqa: E402


def main() -> int:
    settings = Settings()
    warnings = settings.secret_warnings()
    if warnings:
        print("❌ Secret configuration issues detected:")
        for issue in warnings:
            print(f" - {issue}")
        print("\nSet the corresponding environment variables (see README) and rerun.")
        return 1
    print("✅ Secrets are configured with non-default values.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
