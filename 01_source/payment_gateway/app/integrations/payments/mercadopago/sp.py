# 01_source/payment_gateway/app/integrations/payments/mercadopago/sp.py

from app.integrations.payments.mercadopago.client import MercadoPagoClient


def build_provider(access_token: str) -> MercadoPagoClient:
    return MercadoPagoClient(access_token=access_token)
