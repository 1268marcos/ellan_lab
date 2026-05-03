#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

# run from service root: PYTHONPATH=. python validate_ml_data.py


def main() -> int:
    from app.data_quality.feature_validation import run_all_checks
    from app.data_quality.outlier_detection import run_outlier_pipeline

    p = argparse.ArgumentParser(description="Validação e limpeza de features ML")
    p.add_argument("--dry-run", action="store_true", help="Não grava UPDATE nem alertas (IQR)")
    p.add_argument("--skip-outliers", action="store_true", help="Não executa detecção IQR")
    args = p.parse_args()
    rep = run_all_checks()
    print(json.dumps(rep, indent=2, default=str))
    if not args.skip_outliers:
        out = run_outlier_pipeline(dry_run=args.dry_run)
        print(json.dumps(out, indent=2, default=str))
    if rep.get("delay_training"):
        logging.warning("delay_training=1 reason=%s", rep.get("delay_reason"))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
