from pydantic import BaseModel


class ReconcileReport(BaseModel):
    user_id: str
    ledger_sum: int
    wallet_balance: int
    divergent: bool
    rolled_back: bool
