import os
from fastapi import APIRouter, Query, Request

from app.core.antifraud_snapshot import create_daily_snapshot

from app.core.antifraud_snapshot_verify import verify_snapshot_file

router = APIRouter(prefix="/audit", tags=["audit"])

# ANTERIOR
# @router.post("/snapshot")
# def snapshot(
#     machine_id: str = Query("CACIFO-SP-001"),
# ):
#     """
#     Gera snapshot diário antifraude e salva em:
#     - 05_backups/daily/antifraud/
#     - 04_logs/antifraud/
#     """
#     return create_daily_snapshot(machine_id=machine_id)

def _default_machine_id(request: Request) -> str:
    """
    Prioridade:
    1) ENV MACHINE_ID
    2) Inferir pela porta local (8101=SP, 8102=PT)
    3) Fallback seguro
    """
    env_mid = os.getenv("MACHINE_ID")
    if env_mid:
        return env_mid

    # Inferência por porta (funciona quando você acessa http://127.0.0.1:PORT/...)
    port = None
    if request.url and request.url.port:
        port = int(request.url.port)

    if port == 8101:
        return "CACIFO-SP-001"
    if port == 8102:
        return "CACIFO-PT-001"

    return "CACIFO-PT-001"


@router.api_route("/snapshot", methods=["GET", "POST"])
def snapshot(
    request: Request,
    machine_id: str = Query(None),
):
    mid = machine_id or _default_machine_id(request)
    return create_daily_snapshot(machine_id=mid)


@router.api_route("/snapshot/verify_file", methods=["GET", "POST"])
def snapshot_verify_file(
    request: Request,
    machine_id: str = Query(None),
    date_utc: str = Query(..., description="Formato YYYY-MM-DD (UTC)"),
):
    mid = machine_id or _default_machine_id(request)
    return verify_snapshot_file(machine_id=mid, date_utc=date_utc)