from __future__ import annotations

import json
from typing import Any

import urllib.error
import urllib.request


def register_avro_schema(registry_url: str, subject: str, schema: dict[str, Any]) -> int:
    body = json.dumps({"schema": json.dumps(schema)}).encode("utf-8")
    req = urllib.request.Request(
        f"{registry_url.rstrip('/')}/subjects/{subject}/versions",
        data=body,
        headers={"Content-Type": "application/vnd.schemaregistry.v1+json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return int(data.get("id", 0))
    except urllib.error.URLError:
        return 0


def inventory_movement_avro_schema() -> dict[str, Any]:
    return {
        "type": "record",
        "name": "InventoryMovement",
        "namespace": "com.ellan.inventory",
        "fields": [
            {"name": "sku_id", "type": "string"},
            {"name": "delta", "type": "int"},
            {"name": "reason", "type": "string"},
        ],
    }
