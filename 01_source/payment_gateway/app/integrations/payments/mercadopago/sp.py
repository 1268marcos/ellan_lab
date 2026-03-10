from app.integrations.payments.mercadopago.client import MercadoPagoClient


def build_provider(access_token: str) -> MercadoPagoClient:
    return MercadoPagoClient(access_token=access_token)
