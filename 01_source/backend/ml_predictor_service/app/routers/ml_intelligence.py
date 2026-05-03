"""Mock canónico do dashboard ML (DB indisponível ou resposta não serializável)."""
from __future__ import annotations

from typing import Any


def intelligence_dashboard_mock() -> dict[str, Any]:
    return {
        "at_risk_count": 0,
        "at_risk_lockers": [],
        "avg_health_series": [],
        "avg_health_score_series_7d": [],
        "avg_health_score_series_30d": [],
        "active_model": None,
        "last_prediction_at": None,
        "active_accuracy": None,
        "top5_worst_health": [],
    }
