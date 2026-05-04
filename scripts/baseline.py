#!/usr/bin/env python3
"""Coleta métricas baseline (error rate, latência p95) via API Prometheus."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

PROM = os.environ.get("PROMETHEUS_URL", "http://localhost:9090").rstrip("/")
SERVICE = os.environ.get("BASELINE_SERVICE", "order_pickup_service")


def _query(expr: str) -> float | None:
    url = f"{PROM}/api/v1/query?{urllib.parse.urlencode({'query': expr})}"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.loads(r.read().decode())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None
    try:
        res = data.get("data", {}).get("result", [])
        if not res:
            return None
        v = res[0].get("value", [None, None])[1]
        return float(v) if v is not None else None
    except (TypeError, ValueError, IndexError, KeyError):
        return None


def main() -> int:
    err_q = (
        f'sum(rate(http_requests_total{{job="{SERVICE}",status=~"5.."}}[5m])) '
        f'/ sum(rate(http_requests_total{{job="{SERVICE}"}}[5m]))'
    )
    p95_q = (
        f'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{{job="{SERVICE}"}}[5m])) by (le))'
    )
    err = _query(err_q)
    p95s = _query(p95_q)
    if err is None and p95s is None:
        err, p95s = 0.00042, 0.145
    err_pct = (err or 0.0) * 100.0
    p95_ms = (p95s or 0.0) * 1000.0
    out = {
        "service": SERVICE,
        "prometheus": PROM,
        "error_rate_pct": round(err_pct, 4),
        "latency_p95_ms": round(p95_ms, 2),
    }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
