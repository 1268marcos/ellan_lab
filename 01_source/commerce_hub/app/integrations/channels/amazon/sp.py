from app.integrations.channels.base.contracts import ImportOrdersCommand, ChannelOrderResult


class AmazonSPClient:
    provider_name = "amazon"

    def import_orders(self, command: ImportOrdersCommand) -> list[ChannelOrderResult]:
        return []
