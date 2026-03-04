from pydantic import BaseModel
import os

class Settings(BaseModel):
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/orders.db")
    pickup_window_sec: int = int(os.getenv("PICKUP_WINDOW_SEC", "7200"))  # 2h
    pickup_token_ttl_sec: int = int(os.getenv("PICKUP_TOKEN_TTL_SEC", "600"))  # 10min
    service_name: str = os.getenv("SERVICE_NAME", "order_pickup_service")

    # (PROPOSTO) endpoints dos totens
    backend_sp_internal: str = os.getenv("BACKEND_SP_INTERNAL", "http://backend_sp:8000") # porta interna para rodar no docker - 8201 é porta publicada/externo e funciona ex. em http://localhost:8201/docs
    backend_pt_internal: str = os.getenv("BACKEND_PT_INTERNAL", "http://backend_pt:8000") # porta interna para rodar no docker - 8202 é porta publicada/externo e funciona ex. em http://localhost:8202/docs

settings = Settings()