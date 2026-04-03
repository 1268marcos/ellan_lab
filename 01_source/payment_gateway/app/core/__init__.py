# 01_source/payment_gateway/app/core/__init__.py

from app.core.config import settings, BACKEND_BR, BACKEND_SP, BACKEND_PT, REGIONAL_BACKENDS

__all__ = ["settings", "BACKEND_BR", "BACKEND_SP", "BACKEND_PT", "REGIONAL_BACKENDS"]