"""Idempotent backfill: last N calendar days via refresh_ml_features_daily_70d."""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone

from app.db_ml import ml_connection, refresh_features_70d, refresh_mat_view


def backfill_days(n: int = 90, end: date | None = None) -> int:
    end = end or datetime.now(timezone.utc).date()
    start = end - timedelta(days=n - 1)
    total = 0
    with ml_connection() as conn:
        refresh_mat_view(conn)
        total += refresh_features_70d(conn, start.isoformat(), end.isoformat())
    return total


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=90)
    p.add_argument("--end", type=str, default=None, help="YYYY-MM-DD inclusive")
    args = p.parse_args()
    end = date.fromisoformat(args.end) if args.end else None
    n = backfill_days(args.days, end)
    print(n)


if __name__ == "__main__":
    main()
