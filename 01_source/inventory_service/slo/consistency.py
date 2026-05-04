from __future__ import annotations


def within_consistency_slo(divergent: float, total: float, max_rate: float = 0.0001) -> bool:
    if total <= 0:
        return True
    return (divergent / total) < max_rate
