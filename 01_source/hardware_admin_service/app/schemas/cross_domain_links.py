from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DomainReachabilityOut(BaseModel):
    domain: str
    reachable: bool
    detail: str | None = None


class DomainReferenceVerificationOut(BaseModel):
    reference_id: str
    locker_id: str
    domain_type: str
    external_id: str
    external_code: str | None
    status: str
    detail: str | None = None
    remote_snapshot: dict[str, Any] | None = None


class PaymentBindingSyncOut(BaseModel):
    locker_id: str | None
    dry_run: bool
    gateway_methods: int
    inserted: int
    updated: int
    skipped: int
    hardware_only: list[str] = Field(default_factory=list)
    conflicts: list[dict[str, Any]] = Field(default_factory=list)


class CrossDomainGapItemOut(BaseModel):
    locker_id: str
    gap_type: str
    severity: str
    message: str
    suggested_action: str | None = None


class CrossDomainGapsScanOut(BaseModel):
    lockers_scanned: int
    gaps: list[CrossDomainGapItemOut]
    total: int
    domain_reachability: list[DomainReachabilityOut] = Field(default_factory=list)


class Locker360RemoteOut(BaseModel):
    payment_gateway: dict[str, Any] = Field(default_factory=dict)
    order_pickup: dict[str, Any] = Field(default_factory=dict)
    payments_context: dict[str, Any] = Field(default_factory=dict)
    finance_catalog: dict[str, Any] = Field(default_factory=dict)
    partner_ecosystem: dict[str, Any] = Field(default_factory=dict)
    marketplace: dict[str, Any] = Field(default_factory=dict)
    ml: dict[str, Any] = Field(default_factory=dict)
    fiscal: dict[str, Any] = Field(default_factory=dict)


class Locker360Out(BaseModel):
    locker_id: str
    runtime: dict[str, Any] | None = None
    local: dict[str, Any] = Field(default_factory=dict)
    remote: Locker360RemoteOut = Field(default_factory=Locker360RemoteOut)
    gaps: list[CrossDomainGapItemOut] = Field(default_factory=list)
    domain_verifications: list[DomainReferenceVerificationOut] = Field(default_factory=list)


class EcosystemAlignmentItemOut(BaseModel):
    hardware_player_code: str
    hardware_player_id: str
    partner_player_code: str | None = None
    partner_player_id: str | None = None
    match_field: str | None = None
    finance_catalog_code: str | None = None
    locker_operator_ref: str | None = None


class EcosystemAlignmentOut(BaseModel):
    matched: list[EcosystemAlignmentItemOut]
    unmatched_hardware: list[str]
    apply: bool
    metadata_updated: int = 0
