# 01_source/backend/billing_fiscal_service/app/run_invoice_event_worker.py
from __future__ import annotations

import logging
import os

from app.services.invoice_event_worker import run_invoice_event_worker_forever


def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    poll_interval_sec = int(os.getenv("INVOICE_EVENT_WORKER_POLL_SEC", "10"))
    batch_size = int(os.getenv("INVOICE_EVENT_WORKER_BATCH_SIZE", "100"))

    run_invoice_event_worker_forever(
        poll_interval_sec=poll_interval_sec,
        batch_size=batch_size,
    )


if __name__ == "__main__":
    main()
