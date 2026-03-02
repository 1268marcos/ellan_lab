from pydantic import BaseModel
import os

class Settings(BaseModel):
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/orders.db")
    pickup_window_sec: int = int(os.getenv("PICKUP_WINDOW_SEC", "7200"))  # 2h
    pickup_token_ttl_sec: int = int(os.getenv("PICKUP_TOKEN_TTL_SEC", "600"))  # 10min
    service_name: str = os.getenv("SERVICE_NAME", "order_pickup_service")

    # (PROPOSTO) endpoints dos totens
    backend_sp_base: str = os.getenv("BACKEND_SP_BASE", "http://backend_sp:8101")
    backend_pt_base: str = os.getenv("BACKEND_PT_BASE", "http://backend_pt:8102")

settings = Settings()