from app.integrations.channels.base.contracts import ImportOrdersCommand, ChannelOrderResult


class WortenPTClient:
    provider_name = "worten"

    def import_orders(self, command: ImportOrdersCommand) -> list[ChannelOrderResult]:
        return []
