from __future__ import annotations

from prometheus_client import Counter, Gauge

reservations_created = Counter("inventory_reservations_created_total", "Reservations created", ["state"])
stream_consumed = Counter("inventory_stream_messages_consumed_total", "Stream messages consumed", ["event"])
stream_errors = Counter("inventory_stream_errors_total", "Stream consumer errors")
reconciliation_divergences = Gauge("inventory_reconciliation_divergences", "SKUs with movement vs on-hand mismatch")


def inc_reservation(state: str = "pending") -> None:
    reservations_created.labels(state=state).inc()


def inc_stream(event: str) -> None:
    stream_consumed.labels(event=event).inc()


def inc_stream_error() -> None:
    stream_errors.inc()


def set_divergences(n: int) -> None:
    reconciliation_divergences.set(n)
