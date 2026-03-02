from importlib.metadata import version
from typing import Dict, Any
import os
from datetime import datetime

def get_version() -> str:
    """Retorna a versão atual da aplicação."""
    try:
        # Tenta pegar do arquivo de versão ou do ambiente
        return os.getenv("APP_VERSION", "0.1.0")
    except:
        return "0.1.0"

def get_app_info() -> Dict[str, Any]:
    """Retorna informações completas da aplicação."""
    return {
        "name": "payment_gateway",
        "version": get_version(),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "timestamp": None  # será preenchido na resposta
    }