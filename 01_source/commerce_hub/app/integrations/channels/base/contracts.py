from dataclasses import dataclass
from typing import Protocol


@dataclass
class ImportOrdersCommand:
    account_id: str
    country: str


@dataclass
class ChannelOrderResult:
    provider: str
    external_order_id: str
    status: str
    raw_status: str


class ChannelProvider(Protocol):
    provider_name: str

    def import_orders(self, command: ImportOrdersCommand) -> list[ChannelOrderResult]:
        ...
