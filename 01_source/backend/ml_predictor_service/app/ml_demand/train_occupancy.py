"""CLI: PYTHONPATH=. python -m app.ml_demand.train_occupancy"""
from __future__ import annotations

import logging

from app.ml_demand.lstm_demand_model import train_and_save

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    meta = train_and_save()
    logger.info("done: %s", meta)


if __name__ == "__main__":
    main()
