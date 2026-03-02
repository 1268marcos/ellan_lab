from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict


Severity = Literal["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
Decision = Literal["ALLOW", "CHALLENGE", "BLOCK"]
Result = Literal["approved", "requires_confirmation", "rejected"]


class RiskReason(BaseModel):
    code: str
    weight: int
    detail: Optional[str] = None


class RiskPolicy(BaseModel):
    policy_id: str
    thresholds: Dict[str, int]


class RiskSignals(BaseModel):
    device_hash: Optional[str] = None
    ip_hash: Optional[str] = None
    velocity: Dict[str, int] = Field(default_factory=dict)


class RiskAssessment(BaseModel):
    decision: Decision
    score: int = Field(ge=0, le=100)
    score_range: str = "0-100"
    reasons: List[RiskReason] = Field(default_factory=list)
    signals: Optional[RiskSignals] = None
    policy: RiskPolicy


class AntiReplay(BaseModel):
    status: Literal["new", "replayed", "payload_mismatch"]
    idempotency_key: str
    payload_hash: str
    original_payload_hash: Optional[str] = None


class AuditChain(BaseModel):
    prev_hash: Optional[str] = None
    hash: Optional[str] = None
    salt_fingerprint: Optional[str] = None


class AuditInfo(BaseModel):
    audit_event_id: str
    chain: AuditChain = Field(default_factory=AuditChain)


class PaymentInfo(BaseModel):
    status: str
    gateway_status: Optional[str] = None
    metodo: str
    valor: float
    currency: str = "BRL"
    porta: int
    backend: Optional[Dict[str, Any]] = None
    transaction_id: Optional[str] = None


class ErrorInfo(BaseModel):
    type: str
    message: str
    retryable: bool = False


class GatewayPaymentResponse(BaseModel):
    # Permite campos extras sem quebrar (bom pra evolução)
    model_config = ConfigDict(extra="allow")

    request_id: str
    region: str
    service: str
    endpoint: str
    timestamp: float

    result: Result

    payment: Optional[PaymentInfo] = None
    error: Optional[ErrorInfo] = None

    anti_replay: AntiReplay
    risk: RiskAssessment

    severity: Severity
    severity_code: str

    audit: AuditInfo

    actions: Optional[List[Dict[str, Any]]] = None


class HealthResponse(BaseModel):
    status: str
    service: str = "payment_gateway"
    version: str = "1.0.0"