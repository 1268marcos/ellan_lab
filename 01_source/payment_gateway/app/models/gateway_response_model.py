# 01_source/payment_gateway/app/models/gateway_response_model.py
# 07/04/2026 - ajuste do model de resposta

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


Severity = Literal["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
Decision = Literal["ALLOW", "CHALLENGE", "BLOCK"]
Result = Literal[
    "approved",
    "requires_confirmation",
    "rejected",
    "pending_customer_action",
    "pending_provider_confirmation",
    "awaiting_integration",
]


class RiskReason(BaseModel):
    code: str
    weight: int
    detail: Optional[str] = None


class RiskPolicy(BaseModel):
    policy_id: str
    thresholds: Dict[str, int]


class RiskSignals(BaseModel):
    region: Optional[str] = None
    channel: Optional[str] = None
    payment_method: Optional[str] = None
    card_type: Optional[str] = None
    integration_status: Optional[str] = None
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
    status: Literal["new", "replayed", "payload_mismatch", "not_evaluated"]
    idempotency_key: str
    payload_hash: Optional[str] = None
    original_payload_hash: Optional[str] = None


class AuditChain(BaseModel):
    prev_hash: Optional[str] = None
    hash: Optional[str] = None
    salt_fingerprint: Optional[str] = None


class AuditInfo(BaseModel):
    audit_event_id: str
    chain: AuditChain = Field(default_factory=AuditChain)
    log_event_id: Optional[str] = None


class LockerAddressInfo(BaseModel):
    address: Optional[str] = None
    number: Optional[str] = None
    additional_information: Optional[str] = None
    locality: Optional[str] = None
    city: Optional[str] = None
    federative_unit: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None


class LockerInfo(BaseModel):
    locker_id: str
    region: str
    # site_id: str
    site_id: Optional[str] = None
    display_name: str
    backend_region: str
    slots: int
    channels: List[str] = Field(default_factory=list)
    payment_methods: List[str] = Field(default_factory=list)
    active: bool
    address: LockerAddressInfo


class PaymentInfo(BaseModel):
    status: str
    gateway_status: Optional[str] = None
    metodo: str
    valor: float
    currency: str = "BRL"
    porta: int
    card_type: Optional[str] = None
    backend: Optional[Dict[str, Any]] = None
    locker_effect: Optional[Dict[str, Any]] = None
    transaction_id: Optional[str] = None
    instruction_type: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class ErrorInfo(BaseModel):
    type: str
    message: str
    retryable: bool = False
    details: Optional[Dict[str, Any]] = None


class GatewayPaymentResponse(BaseModel):
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
    risk: Optional[RiskAssessment] = None

    locker: Optional[LockerInfo] = None

    severity: Severity
    severity_code: str

    audit: AuditInfo

    actions: Optional[List[Dict[str, Any]]] = None


class HealthResponse(BaseModel):
    status: str
    service: str = "payment_gateway"
    version: str = "1.0.0"