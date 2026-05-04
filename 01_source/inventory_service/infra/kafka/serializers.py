from __future__ import annotations

import json
from typing import Any


def json_dumps(value: Any) -> bytes:
    return json.dumps(value, separators=(",", ":"), default=str).encode("utf-8")


def json_loads(raw: bytes) -> Any:
    return json.loads(raw.decode("utf-8"))
