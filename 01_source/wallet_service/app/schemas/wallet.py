from pydantic import BaseModel, Field


class BalanceOut(BaseModel):
    user_id: str
    balance: int
    version: int


class CreditBody(BaseModel):
    user_id: str
    amount: int = Field(gt=0)
    transaction_id: str


class DebitBody(BaseModel):
    user_id: str
    amount: int = Field(gt=0)
    transaction_id: str
    version: int | None = None


class ApplyCreditBody(BaseModel):
    user_id: str
    credit_id: str
    transaction_id: str


class ExpiredPickupBody(BaseModel):
    user_id: str
    amount: int = Field(gt=0)
    transaction_id: str
