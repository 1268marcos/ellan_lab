#!/usr/bin/env python3
"""Materializa fixtures JSON FG-1 em fixtures/fiscal/fg1/ (alinhado à matriz canônica)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.fiscal_fg1_stub_service import (  # noqa: E402
    FG1_WAVE_COUNTRIES,
    _scenario_map,
    build_fg1_fixture_document,
)


def main() -> int:
    out_root = ROOT / "fixtures" / "fiscal" / "fg1"
    out_root.mkdir(parents=True, exist_ok=True)
    scenarios = _scenario_map()
    n = 0
    for country in FG1_WAVE_COUNTRIES:
        for scenario_code, row in scenarios.items():
            op = row["operation"]
            doc = build_fg1_fixture_document(country, op, scenario_code)
            target = out_root / country.lower() / op / f"{scenario_code.lower()}.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            n += 1
    print(f"OK: wrote {n} fixtures under {out_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
