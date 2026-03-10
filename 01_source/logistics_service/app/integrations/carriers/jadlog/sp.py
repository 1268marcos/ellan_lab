from app.integrations.carriers.base.contracts import CreateShipmentCommand, ShipmentResult


class JadlogSPClient:
    provider_name = "jadlog"

    def create_shipment(self, command: CreateShipmentCommand) -> ShipmentResult:
        return ShipmentResult(
            provider=self.provider_name,
            provider_shipment_id=f"jadlog_{command.shipment_id}",
            status="CREATED",
            tracking_code=f"JAD-{command.shipment_id}",
        )
