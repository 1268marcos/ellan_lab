from app.integrations.carriers.base.contracts import CreateShipmentCommand, ShipmentResult


class FedexSPClient:
    provider_name = "fedex"

    def create_shipment(self, command: CreateShipmentCommand) -> ShipmentResult:
        return ShipmentResult(
            provider=self.provider_name,
            provider_shipment_id=f"fedex_{command.shipment_id}",
            status="CREATED",
            tracking_code=f"FDX-{command.shipment_id}",
        )
