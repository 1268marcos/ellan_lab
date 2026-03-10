from app.integrations.carriers.base.contracts import CreateShipmentCommand, ShipmentResult


class DHLPTClient:
    provider_name = "dhl"

    def create_shipment(self, command: CreateShipmentCommand) -> ShipmentResult:
        return ShipmentResult(
            provider=self.provider_name,
            provider_shipment_id=f"dhl_{command.shipment_id}",
            status="CREATED",
            tracking_code=f"DHL-{command.shipment_id}",
        )
