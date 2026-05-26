from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal


def row_to_dict(row) -> dict:
    out: dict = {}
    for col in row.__table__.columns:
        val = getattr(row, col.key)
        if isinstance(val, (datetime, date)):
            out[col.key] = val.isoformat()
        elif isinstance(val, Decimal):
            out[col.key] = float(val)
        else:
            out[col.key] = val
    return out
