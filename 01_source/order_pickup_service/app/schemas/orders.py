from pydantic import BaseModel
from typing import Optional, Dict, Any

class CreateOrderIn(BaseModel):
    """
    Schema para criação de pedido
    Baseado no payload usado em create_order (linha ~40)
    """
    region: str
    sku_id: str
    totem_id: str
    # O router também pode esperar outros campos, 
    # mas estes são os explicitamente usados

class OrderOut(BaseModel):
    """
    Schema para resposta de pedido
    Baseado nos returns das funções (linhas ~80, ~130, ~180, ~220)
    """
    order_id: str
    channel: str
    status: str
    amount_cents: int
    allocation: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True