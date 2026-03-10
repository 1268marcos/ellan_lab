from dataclasses import dataclass
from typing import Any


@dataclass
class IdempotencyRecord:
    key: str
    fingerprint: str
    response: Any | None = None
    status: str = "PENDING"


class InMemoryIdempotencyStore:
    def __init__(self) -> None:
        self._records: dict[str, IdempotencyRecord] = {}

    def get(self, key: str) -> IdempotencyRecord | None:
        return self._records.get(key)

    def save(self, record: IdempotencyRecord) -> None:
        self._records[record.key] = record
