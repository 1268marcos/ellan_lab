"""CLI: PYTHONPATH=. python -m app.ml_fraud.train_fraud_models"""
from __future__ import annotations

import logging

from app.ml_fraud.fraud_detection_pipeline import train_and_save

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    meta = train_and_save()
    logger.info("done: %s", meta)


if __name__ == "__main__":
    main()
