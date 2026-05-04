from __future__ import annotations


def within_error_rate_slo(errors: float, total: float, max_rate: float = 0.001) -> bool:
    if total <= 0:
        return True
    return (errors / total) < max_rate
