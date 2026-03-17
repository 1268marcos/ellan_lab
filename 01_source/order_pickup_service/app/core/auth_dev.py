# 01_source/order_pickup_service/app/core/auth_dev.py
from fastapi import Request

from app.core.auth_dep import get_current_user
from app.core.config import settings


class DevUser:
    def __init__(self, user_id: str):
        self.id = user_id


def get_current_user_or_dev(request: Request):
    """
    DEV_BYPASS_AUTH=true:
      - não exige bearer token
      - retorna user fake
    caso contrário:
      - exige bearer token via get_current_user
    O que é um "Bearer Token"?
      - Bearer Token é um tipo de "chave de acesso" usada em 
        APIs (especialmente em APIs REST que seguem o padrão OAuth 2.0).
      - É uma string (geralmente longa e criptografada) que o 
        cliente (como um aplicativo ou site) envia para o servidor 
        para provar que tem permissão para acessar aquela informação.
      - O nome "Bearer" (portador) significa: "quem possui este token, 
        possui o acesso". É como um ingresso de show: quem apresenta 
        o ingresso (o token) entra.
      - Normalmente, ele é enviado no cabeçalho (header) da 
        requisição HTTP, no formato: Authorization: Bearer <seu_token_aqui>.
    """
    if settings.dev_bypass_auth:
        return DevUser(user_id=settings.dev_user_id)

    return get_current_user(request)