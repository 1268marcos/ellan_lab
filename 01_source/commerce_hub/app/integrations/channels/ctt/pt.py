from app.integrations.channels.base.contracts import ImportOrdersCommand, ChannelOrderResult


class CTTPTClient:
    provider_name = "ctt"

    def import_orders(self, command: ImportOrdersCommand) -> list[ChannelOrderResult]:
        return []
