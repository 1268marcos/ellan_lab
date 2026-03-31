# 01_source/backend/runtime/app/routers/hardware.py

from __future__ import annotations

"""
Objetivo

Transformar para runtime multi-locker:

receber X-Locker-Id
resolver identidade do locker
publicar no tópico MQTT correto para aquele locker
registrar evento com locker_id/machine_id corretos

Sem isso, ONLINE e KIOSK não fecham consistência operacional completa.

Deve publicar comando MQTT para o locker correto, usando resolução dinâmica.

Hoje esse é um dos principais travamentos para unificação real.
"""


from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel

from app.core.internal_auth import require_internal_token
from app.services.hardware_command_service import execute_hardware_command

router = APIRouter(prefix="/locker", tags=["locker-hardware"])


class CmdOut(BaseModel):
    ok: bool
    service: str
    locker_id: str
    machine_id: str
    region: str
    slot: int
    command: str
    command_id: str
    topic: str
    created_at: str
    state_before_command: str


@router.post("/slots/{slot}/open", response_model=CmdOut)
def open_slot(
    slot: int,
    request: Request,
    x_locker_id: str | None = Header(default=None, alias="X-Locker-Id"),
    _=Depends(require_internal_token),
):
    return execute_hardware_command(
        request=request,
        x_locker_id=x_locker_id,
        slot=slot,
        command="OPEN",
    )


@router.post("/slots/{slot}/light/on", response_model=CmdOut)
def light_on(
    slot: int,
    request: Request,
    x_locker_id: str | None = Header(default=None, alias="X-Locker-Id"),
    _=Depends(require_internal_token),
):
    return execute_hardware_command(
        request=request,
        x_locker_id=x_locker_id,
        slot=slot,
        command="LIGHT_ON",
    )