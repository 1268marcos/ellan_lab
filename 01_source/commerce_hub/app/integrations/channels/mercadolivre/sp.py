from app.integrations.channels.base.contracts import ImportOrdersCommand, ChannelOrderResult


class MercadoLivreSPClient:
    provider_name = "mercadolivre"

    def import_orders(self, command: ImportOrdersCommand) -> list[ChannelOrderResult]:
        return [
            ChannelOrderResult(
                provider=self.provider_name,
                external_order_id="ml_stub_001",
                status="NEW",
                raw_status="stub_new",
            )
        ]
