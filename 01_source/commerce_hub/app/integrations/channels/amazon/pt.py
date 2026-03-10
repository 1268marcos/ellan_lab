from app.integrations.channels.base.contracts import ImportOrdersCommand, ChannelOrderResult


class AmazonPTClient:
    provider_name = "amazon"

    def import_orders(self, command: ImportOrdersCommand) -> list[ChannelOrderResult]:
        return []
