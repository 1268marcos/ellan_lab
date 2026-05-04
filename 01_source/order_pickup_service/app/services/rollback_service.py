from __future__ import annotations

import logging
import time
from collections import deque

from app.config import feature_flags
from app.core.config import settings

logger = logging.getLogger(__name__)

_window: deque[tuple[float, bool]] = deque()


def _prune(now: float) -> None:
    cutoff = now - float(settings.rollback_window_seconds)
    while _window and _window[0][0] < cutoff:
        _window.popleft()


def observe_request_outcome(*, is_error: bool) -> None:
    now = time.time()
    _window.append((now, is_error))
    _prune(now)


def window_error_rate() -> float:
    now = time.time()
    _prune(now)
    if not _window:
        return 0.0
    errs = sum(1 for _, e in _window if e)
    return errs / len(_window)


def should_trigger_rollback() -> bool:
    if not feature_flags.auto_rollback_enabled():
        return False
    if len(_window) < int(settings.rollback_min_samples):
        return False
    return window_error_rate() > float(settings.rollback_error_rate_threshold)


def maybe_execute_rollback() -> bool:
    if not should_trigger_rollback():
        return False
    feature_flags.apply_rollback_all_off()
    logger.error(
        "auto_rollback executed error_rate=%s threshold=%s",
        window_error_rate(),
        settings.rollback_error_rate_threshold,
    )
    return True


def reset_window() -> None:
    _window.clear()
