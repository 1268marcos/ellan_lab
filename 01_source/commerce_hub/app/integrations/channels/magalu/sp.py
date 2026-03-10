from app.integrations.channels.base.contracts import ImportOrdersCommand, ChannelOrderResult


class MagaluSPClient:
    provider_name = "magalu"

    def import_orders(self, command: ImportOrdersCommand) -> list[ChannelOrderResult]:
        return []
