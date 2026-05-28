"""Validação e carga de HEALTH_SCORE_WEIGHTS."""

from __future__ import annotations

import pytest

from app.core.config import Settings
from app.services.pickup_health_service import (
    DEFAULT_HEALTH_SCORE_WEIGHTS,
    configure_health_score_weights,
    get_health_score_weights,
    load_weights,
    validate_health_score_weights,
)


def _settings(weights: str) -> Settings:
    return Settings(HEALTH_SCORE_WEIGHTS=weights)


def test_load_weights_parses_valid_config():
    weights = load_weights(
        _settings("efficiency=0.35,reliability=0.25,risk=0.30,trend=0.10")
    )
    assert weights == {
        "efficiency": 0.35,
        "reliability": 0.25,
        "risk": 0.30,
        "trend": 0.10,
    }


def test_validate_health_score_weights_accepts_defaults():
    validate_health_score_weights(dict(DEFAULT_HEALTH_SCORE_WEIGHTS))


def test_validate_health_score_weights_rejects_sum_not_one():
    bad = dict(DEFAULT_HEALTH_SCORE_WEIGHTS)
    bad["efficiency"] = 0.50
    with pytest.raises(ValueError, match="sum to ~1.0"):
        validate_health_score_weights(bad)


def test_validate_health_score_weights_rejects_out_of_range():
    bad = dict(DEFAULT_HEALTH_SCORE_WEIGHTS)
    bad["risk"] = 1.5
    with pytest.raises(ValueError, match="between 0.0 and 1.0"):
        validate_health_score_weights(bad)


def test_validate_health_score_weights_rejects_missing_key():
    partial = {"efficiency": 0.5, "reliability": 0.5}
    with pytest.raises(ValueError, match="must define exactly"):
        validate_health_score_weights(partial)


def test_load_weights_rejects_malformed_entry():
    with pytest.raises(ValueError, match="invalid health_score_weights entry"):
        load_weights(_settings("efficiency=0.5,not-a-pair"))


def test_configure_health_score_weights_falls_back_on_invalid(monkeypatch):
    monkeypatch.setattr(
        "app.services.pickup_health_service.logger",
        __import__("logging").getLogger("test"),
    )
    configure_health_score_weights(_settings("efficiency=0.9,reliability=0.9,risk=0.9,trend=0.9"))
    assert get_health_score_weights() == DEFAULT_HEALTH_SCORE_WEIGHTS


def test_configure_health_score_weights_applies_valid_config():
    configure_health_score_weights(
        _settings("efficiency=0.35,reliability=0.25,risk=0.30,trend=0.10")
    )
    assert get_health_score_weights() == {
        "efficiency": 0.35,
        "reliability": 0.25,
        "risk": 0.30,
        "trend": 0.10,
    }
