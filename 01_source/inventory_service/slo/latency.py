from __future__ import annotations


def within_latency_slo(p95_ms: float, baseline_ms: float, slack_ms: float = 10.0) -> bool:
    return p95_ms <= baseline_ms + slack_ms
