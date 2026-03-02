from typing import Literal, Optional
from pydantic import BaseModel, Field

class PaymentRequest(BaseModel):
    regiao: Literal["SP", "PT"]                         # str   
    porta: int = Field(ge=1, le=24)                     # Porta do produto escolhido
    metodo: Literal["PIX", "MBWAY", "NFC", "CARTAO"]    # str 
    valor: float = Field(gt=0)

    # opcionais (já deixa pronto sem quebrar)
    currency: Optional[str] = "BRL"
    locker_id: Optional[str] = None