import os
from fastapi import HTTPException, Request, Depends
from app.core.auth_dep import get_current_user

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
    """
    if os.getenv("DEV_BYPASS_AUTH", "false").lower() == "true":
        return DevUser(user_id=os.getenv("DEV_USER_ID", "dev_user_1"))

    # modo normal: exige auth real
    # Chamamos a dependency real explicitamente (sem depender de injection)
    # para não misturar fluxos.
    return get_current_user(request)