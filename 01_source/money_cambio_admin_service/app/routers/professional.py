from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.professional import (
    EcosystemIntelligenceOut,
    EcosystemMatrixOut,
    EcosystemLinkOut,
    EcosystemSegmentListOut,
    EcosystemSegmentOut,
    LockerPlayerListOut,
    LockerPlayerOut,
    PlayerRelationListOut,
    PlayerRelationOut,
    ComplianceLimitIn,
    ComplianceLimitListOut,
    ComplianceLimitOut,
    CorridorMarkupIn,
    CorridorMarkupListOut,
    CorridorMarkupOut,
    FxRateAuditListOut,
    FxRateAuditOut,
    GlobalOpsDashboardOut,
    MethodCountryMatrixIn,
    MethodCountryMatrixListOut,
    MethodCountryMatrixOut,
    OperatingCountryIn,
    OperatingCountryListOut,
    OperatingCountryOut,
    OperatingCountryUpdate,
    PaymentCorridorIn,
    PaymentCorridorListOut,
    PaymentCorridorOut,
    PaymentCorridorUpdate,
    WalletCountryMatrixIn,
    WalletCountryMatrixListOut,
    WalletCountryMatrixOut,
)
from app.services import professional_service as svc

router = APIRouter(tags=["professional"])


@router.get("/global-ops/dashboard", response_model=GlobalOpsDashboardOut)
def global_dashboard(db: Session = Depends(get_db)) -> GlobalOpsDashboardOut:
    return svc.global_dashboard(db)


@router.get("/locker-players", response_model=LockerPlayerListOut)
def list_locker_players(
    segment: str | None = None,
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
) -> LockerPlayerListOut:
    rows = svc.list_locker_players(db, segment=segment, active_only=active_only)
    items = [LockerPlayerOut.model_validate(r) for r in rows]
    return LockerPlayerListOut(items=items, total=len(items))


@router.get("/ecosystem-matrix", response_model=EcosystemMatrixOut)
def ecosystem_matrix(db: Session = Depends(get_db)) -> EcosystemMatrixOut:
    rows = svc.ecosystem_matrix(db)
    items = [EcosystemLinkOut(**r) for r in rows]
    return EcosystemMatrixOut(items=items, total=len(items))


@router.get("/ecosystem-segments", response_model=EcosystemSegmentListOut)
def list_ecosystem_segments(
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
) -> EcosystemSegmentListOut:
    rows = svc.list_ecosystem_segments(db, active_only=active_only)
    items = [EcosystemSegmentOut(**r) for r in rows]
    return EcosystemSegmentListOut(items=items, total=len(items))


@router.get("/player-relations", response_model=PlayerRelationListOut)
def list_player_relations(
    from_player: str | None = None,
    to_player: str | None = None,
    relation_type: str | None = None,
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
) -> PlayerRelationListOut:
    rows = svc.list_player_relations(
        db,
        from_player=from_player,
        to_player=to_player,
        relation_type=relation_type,
        active_only=active_only,
    )
    items = [PlayerRelationOut.model_validate(r) for r in rows]
    return PlayerRelationListOut(items=items, total=len(items))


@router.get("/ecosystem-intelligence", response_model=EcosystemIntelligenceOut)
def ecosystem_intelligence(db: Session = Depends(get_db)) -> EcosystemIntelligenceOut:
    return EcosystemIntelligenceOut(**svc.ecosystem_intelligence(db))


@router.get("/operating-countries", response_model=OperatingCountryListOut)
def list_operating_countries(
    active_only: bool = Query(False),
    regulatory_zone: str | None = None,
    db: Session = Depends(get_db),
) -> OperatingCountryListOut:
    rows = svc.list_countries(db, active_only=active_only, zone=regulatory_zone)
    items = [OperatingCountryOut.model_validate(r) for r in rows]
    return OperatingCountryListOut(items=items, total=len(items))


@router.post("/operating-countries", response_model=OperatingCountryOut, status_code=status.HTTP_201_CREATED)
def create_operating_country(body: OperatingCountryIn, db: Session = Depends(get_db)) -> OperatingCountryOut:
    return OperatingCountryOut.model_validate(svc.create_country(db, body))


@router.patch("/operating-countries/{country_code}", response_model=OperatingCountryOut)
def update_operating_country(
    country_code: str, body: OperatingCountryUpdate, db: Session = Depends(get_db)
) -> OperatingCountryOut:
    return OperatingCountryOut.model_validate(svc.update_country(db, country_code, body))


@router.get("/method-country-matrix", response_model=MethodCountryMatrixListOut)
def list_method_matrix(
    country_code: str | None = None,
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
) -> MethodCountryMatrixListOut:
    rows = svc.list_method_matrix(db, country_code=country_code, active_only=active_only)
    items = [MethodCountryMatrixOut.model_validate(r) for r in rows]
    return MethodCountryMatrixListOut(items=items, total=len(items))


@router.post("/method-country-matrix", response_model=MethodCountryMatrixOut, status_code=status.HTTP_201_CREATED)
def create_method_matrix(body: MethodCountryMatrixIn, db: Session = Depends(get_db)) -> MethodCountryMatrixOut:
    return MethodCountryMatrixOut.model_validate(svc.create_method_matrix(db, body))


@router.delete("/method-country-matrix/{row_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_method_matrix(row_id: int, db: Session = Depends(get_db)) -> None:
    svc.delete_method_matrix(db, row_id)


@router.get("/wallet-country-matrix", response_model=WalletCountryMatrixListOut)
def list_wallet_matrix(
    country_code: str | None = None, db: Session = Depends(get_db)
) -> WalletCountryMatrixListOut:
    rows = svc.list_wallet_matrix(db, country_code=country_code)
    items = [WalletCountryMatrixOut.model_validate(r) for r in rows]
    return WalletCountryMatrixListOut(items=items, total=len(items))


@router.post("/wallet-country-matrix", response_model=WalletCountryMatrixOut, status_code=status.HTTP_201_CREATED)
def create_wallet_matrix(body: WalletCountryMatrixIn, db: Session = Depends(get_db)) -> WalletCountryMatrixOut:
    return WalletCountryMatrixOut.model_validate(svc.create_wallet_matrix(db, body))


@router.get("/payment-corridors", response_model=PaymentCorridorListOut)
def list_payment_corridors(
    origin_country_code: str | None = None,
    destination_country_code: str | None = None,
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
) -> PaymentCorridorListOut:
    rows = svc.list_corridors(
        db, origin=origin_country_code, destination=destination_country_code, active_only=active_only
    )
    items = [PaymentCorridorOut.model_validate(r) for r in rows]
    return PaymentCorridorListOut(items=items, total=len(items))


@router.post("/payment-corridors", response_model=PaymentCorridorOut, status_code=status.HTTP_201_CREATED)
def create_payment_corridor(body: PaymentCorridorIn, db: Session = Depends(get_db)) -> PaymentCorridorOut:
    return PaymentCorridorOut.model_validate(svc.create_corridor(db, body))


@router.patch("/payment-corridors/{corridor_id}", response_model=PaymentCorridorOut)
def update_payment_corridor(
    corridor_id: str, body: PaymentCorridorUpdate, db: Session = Depends(get_db)
) -> PaymentCorridorOut:
    return PaymentCorridorOut.model_validate(svc.update_corridor(db, corridor_id, body))


@router.get("/payment-corridors/markups", response_model=CorridorMarkupListOut)
def list_corridor_markups(
    corridor_id: str | None = None, db: Session = Depends(get_db)
) -> CorridorMarkupListOut:
    rows = svc.list_corridor_markups(db, corridor_id=corridor_id)
    items = [CorridorMarkupOut.model_validate(r) for r in rows]
    return CorridorMarkupListOut(items=items, total=len(items))


@router.post("/payment-corridors/markups", response_model=CorridorMarkupOut, status_code=status.HTTP_201_CREATED)
def create_corridor_markup(body: CorridorMarkupIn, db: Session = Depends(get_db)) -> CorridorMarkupOut:
    return CorridorMarkupOut.model_validate(svc.create_corridor_markup(db, body))


@router.get("/compliance-limits", response_model=ComplianceLimitListOut)
def list_compliance_limits(
    country_code: str | None = None, db: Session = Depends(get_db)
) -> ComplianceLimitListOut:
    rows = svc.list_compliance(db, country_code=country_code)
    items = [ComplianceLimitOut.model_validate(r) for r in rows]
    return ComplianceLimitListOut(items=items, total=len(items))


@router.post("/compliance-limits", response_model=ComplianceLimitOut, status_code=status.HTTP_201_CREATED)
def create_compliance_limit(body: ComplianceLimitIn, db: Session = Depends(get_db)) -> ComplianceLimitOut:
    return ComplianceLimitOut.model_validate(svc.create_compliance(db, body))


@router.get("/fx-rate-audit", response_model=FxRateAuditListOut)
def list_fx_rate_audit(limit: int = Query(50, le=200), db: Session = Depends(get_db)) -> FxRateAuditListOut:
    rows = svc.list_fx_audit(db, limit=limit)
    items = [FxRateAuditOut.model_validate(r) for r in rows]
    return FxRateAuditListOut(items=items, total=len(items))
