#!/usr/bin/env python3
"""Worker diário: treina modelo com dados até ontem (cron 02:00 ou APScheduler no main)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.train_job import run_training_job  # noqa: E402


def main() -> None:
    out = run_training_job()
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
