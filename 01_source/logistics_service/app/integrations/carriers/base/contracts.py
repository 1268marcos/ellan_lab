from dataclasses import dataclass
from typing import Protocol


@dataclass
class CreateShipmentCommand:
    shipment_id: str
    country: str
    recipient_name: str
    address_line: str
    postal_code: str
    city: str


@dataclass
class ShipmentResult:
    provider: str
    provider_shipment_id: str
    status: str
    tracking_code: str | None = None


class CarrierProvider(Protocol):
    provider_name: str

    def create_shipment(self, command: CreateShipmentCommand) -> ShipmentResult:
        ...
