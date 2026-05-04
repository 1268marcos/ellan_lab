#!/usr/bin/env python3
"""Drain monolith credit bridge assumptions: verify wallet-service before USE_WALLET_SERVICE."""

from __future__ import annotations

import os
import sys

import httpx


def main() -> int:
    base = os.environ.get("WALLET_SERVICE_BASE_URL", "http://127.0.0.1:8004").rstrip("/")
    try:
        with httpx.Client(timeout=30.0) as c:
            r = c.get(f"{base}/health/ready")
            r.raise_for_status()
    except Exception as exc:
        print(f"migrate_wallet: wallet not reachable: {exc}", file=sys.stderr)
        return 1
    print("migrate_wallet: ok (bridge→API); USE_WALLET_SERVICE=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
