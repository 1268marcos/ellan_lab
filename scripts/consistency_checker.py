#!/usr/bin/env python3
"""Exit 1 if migration divergence ratio > threshold (default 0.01%)."""

from __future__ import annotations

import argparse
import os
import sys


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--threshold", type=float, default=float(os.environ.get("DIVERGENCE_THRESHOLD", "0.0001")))
    p.add_argument("--divergence-price", type=float, default=float(os.environ.get("DIVERGENCE_PRICE", "0.0")))
    p.add_argument("--total-orders", type=float, default=float(os.environ.get("TOTAL_ORDERS", "1.0")))
    args = p.parse_args()
    denom = args.total_orders if args.total_orders > 0 else 1.0
    ratio = args.divergence_price / denom
    if ratio > args.threshold:
        print(f"consistency_checker: ALERT divergence_ratio={ratio:.6f} > {args.threshold}", file=sys.stderr)
        return 1
    print(f"consistency_checker: ok ratio={ratio:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
