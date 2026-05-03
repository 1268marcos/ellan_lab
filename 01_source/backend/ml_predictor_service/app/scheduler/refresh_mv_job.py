"""Daily job: REFRESH MV + 70d feature upsert (intended for cron 01:00 UTC)."""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone

from app.db_ml import ml_connection, refresh_features_70d, refresh_mat_view


def _utc_today() -> date:
    return datetime.now(timezone.utc).date()


def run_daily(as_of: date | None = None) -> None:
    as_of = as_of or _utc_today()
    d0 = as_of - timedelta(days=8)
    d1 = as_of - timedelta(days=1)
    with ml_connection() as conn:
        refresh_mat_view(conn)
        refresh_features_70d(conn, d0.isoformat(), d1.isoformat())


def main() -> None:
    p = argparse.ArgumentParser(description="ML MV refresh + 70d upsert (run at 01:00 UTC)")
    p.add_argument("--as-of", type=str, default=None, help="YYYY-MM-DD (default: today UTC)")
    args = p.parse_args()
    as_of = date.fromisoformat(args.as_of) if args.as_of else None
    run_daily(as_of)


if __name__ == "__main__":
    main()
