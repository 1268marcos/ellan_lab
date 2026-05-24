from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.clients.finance_admin_client import FinanceAdminClientError
from app.core.database import get_db
from app.schemas.finance_sync import FinanceSyncOut, FinanceSyncStatusOut
from app.services import finance_sync_service as sync_svc

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/finance-admin", response_model=FinanceSyncOut)
def sync_finance_admin(
    trigger_finance_sync: bool = Query(True, description="POST sync no Finance antes de ler catálogo"),
    create_finance_partners: bool = Query(False),
    deactivate_missing: bool = Query(False, description="Desativa players só do Finance ausentes no catálogo"),
    db: Session = Depends(get_db),
) -> FinanceSyncOut:
    try:
        return sync_svc.sync_from_finance_admin(
            db,
            trigger_finance_sync=trigger_finance_sync,
            create_finance_partners=create_finance_partners,
            deactivate_missing=deactivate_missing,
        )
    except FinanceAdminClientError as exc:
        from app.core.config import get_settings

        base = get_settings().finance_admin_base_url
        hint = (
            f"{exc}. Verifique finance-admin em {base} "
            "(local: uvicorn na porta 8123). Docker/WSL: extra_hosts host.docker.internal:host-gateway."
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=hint,
        ) from exc


@router.get("/finance-admin/status", response_model=FinanceSyncStatusOut)
def finance_sync_status() -> FinanceSyncStatusOut:
    from app.core.config import get_settings

    s = get_settings()
    return FinanceSyncStatusOut(
        finance_admin_base_url=s.finance_admin_base_url,
        finance_admin_sync_enabled=s.finance_admin_sync_enabled,
        last_sync=sync_svc.get_last_finance_sync(),
    )
