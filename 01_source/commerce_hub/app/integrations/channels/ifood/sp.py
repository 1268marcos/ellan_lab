from app.integrations.channels.base.contracts import ImportOrdersCommand, ChannelOrderResult


class IFoodSPClient:
    provider_name = "ifood"

    def import_orders(self, command: ImportOrdersCommand) -> list[ChannelOrderResult]:
        return []
