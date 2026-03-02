from importlib.metadata import version
from typing import Dict, Any
import os
from datetime import datetime

def get_version() -> str:
    """Retorna a versão atual da aplicação."""
    try:
        # Tenta pegar do arquivo de versão ou do ambiente
        return os.getenv("APP_VERSION", "0.1.0")  # version("app")
    except:
        return "0.1.0"  # versão padrão

def get_app_info() -> Dict[str, Any]:
    """Retorna informações completas da aplicação."""
    return {
        "name": "order_pickup_service",
        "version": get_version(),
        "environment": os.getenv("ENVIRONMENT", "development"),  # ou production, testing
        "timestamp": None  # será preenchido na resposta
    }