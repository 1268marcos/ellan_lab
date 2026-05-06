from __future__ import annotations

import asyncio
import hashlib
import logging
from typing import Any

import httpx
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.internal_auth import require_internal_token
from app.services import partner_data_service
from app.services import partner_client
from app.workers.consistency_checker import compare_schemas

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["partners"])
partner_v1_router = APIRouter(prefix="/api/partner/v1", tags=["partners"])
internal_router = APIRouter(prefix="/internal/partners", tags=["partners-shadow"])

SHADOW_KEYS = ("id", "name", "partner_type", "legal_name", "contact_email", "status")


class ShadowCompareIn(BaseModel):
    legacy: dict[str, Any] = Field(default_factory=dict)
    remote: dict[str, Any] = Field(default_factory=dict)


class ShadowCompareOut(BaseModel):
    divergences: list[str]


class PartnerLoginIn(BaseModel):
    partner_id: str = Field(min_length=1, max_length=64)
    api_key: str = Field(min_length=8, max_length=256)


class PartnerLoginOut(BaseModel):
    token: str
    access_token: str
    partner_name: str
    profile: str
    role: str


def _require_partner_auth(
    partner_id: str,
    db: Session,
    x_api_key: str | None,
) -> partner_data_service.PartnerAuthContext:
    return partner_data_service.validate_partner_access(db=db, partner_id=partner_id, raw_api_key=str(x_api_key or ""))


def _infer_profile(partner_id: str) -> str:
    pid = str(partner_id or "").lower()
    if "admin" in pid:
        return "admin"
    if "ops" in pid:
        return "ops"
    return "partner"


async def async_compare_partner_payloads(
    legacy: dict[str, Any],
    remote: dict[str, Any],
    keys: tuple[str, ...] = SHADOW_KEYS,
) -> list[str]:
    return await asyncio.to_thread(compare_schemas, legacy, remote, keys)


@router.post("/partners/login", response_model=PartnerLoginOut)
def partner_login(payload: PartnerLoginIn, db: Session = Depends(get_db)) -> PartnerLoginOut:
    partner_id = str(payload.partner_id or "").strip()
    api_key = str(payload.api_key or "").strip()
    if not partner_id or not api_key:
        raise HTTPException(status_code=422, detail="partner_id and api_key are required")

    key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
    key_row = db.execute(
        text(
            """
            SELECT id
            FROM partner_api_keys
            WHERE partner_id = :partner_id
              AND key_hash = :key_hash
              AND revoked_at IS NULL
              AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY created_at DESC
            LIMIT 1
            """
        ),
        {"partner_id": partner_id, "key_hash": key_hash},
    ).mappings().first()
    if not key_row:
        raise HTTPException(status_code=401, detail="invalid partner_id/api_key")

    partner_name_row = db.execute(
        text(
            """
            SELECT name
            FROM ecommerce_partners
            WHERE id = :partner_id
            LIMIT 1
            """
        ),
        {"partner_id": partner_id},
    ).mappings().first()
    partner_name = str((partner_name_row or {}).get("name") or partner_id)

    profile = _infer_profile(partner_id)
    return PartnerLoginOut(
        token=api_key,
        access_token=api_key,
        partner_name=partner_name,
        profile=profile,
        role=profile,
    )


@router.get("/partners/{partner_id}")
async def get_partner_via_service(partner_id: str) -> dict[str, Any]:
    if settings.use_partner_service:
        url = f"{settings.partner_service_base_url.rstrip('/')}/api/v1/partners/{partner_id}"
        async with httpx.AsyncClient(timeout=float(settings.backend_client_timeout_sec)) as client:
            r = await client.get(url)
            if r.status_code == 404:
                raise HTTPException(status_code=404, detail="partner not found")
            r.raise_for_status()
            data = r.json()
            if not isinstance(data, dict):
                raise HTTPException(status_code=502, detail="invalid partner payload")
            return data
    data = await asyncio.to_thread(partner_client.fetch_partner_safe, partner_id=partner_id)
    if not data:
        raise HTTPException(status_code=404, detail="partner not found")
    return data


@partner_v1_router.get("/lockers/{locker_id}/summary")
def get_partner_locker_summary(
    locker_id: str,
    partner_id: Annotated[str, Query(min_length=1, max_length=64)],
    db: Session = Depends(get_db),
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> dict[str, Any]:
    auth_ctx = _require_partner_auth(partner_id=partner_id, db=db, x_api_key=x_api_key)
    return partner_data_service.get_locker_summary(
        db=db,
        locker_id=locker_id,
        partner_id=auth_ctx.partner_id,
    )


@partner_v1_router.get("/pickups/active")
def get_partner_active_pickups(
    partner_id: Annotated[str, Query(min_length=1, max_length=64)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    db: Session = Depends(get_db),
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> dict[str, Any]:
    auth_ctx = _require_partner_auth(partner_id=partner_id, db=db, x_api_key=x_api_key)
    return partner_data_service.get_active_pickups(
        db=db,
        partner_id=auth_ctx.partner_id,
        limit=limit,
    )


@internal_router.post("/shadow-compare", response_model=ShadowCompareOut)
async def shadow_compare(
    body: ShadowCompareIn,
    _: bool = Depends(require_internal_token),
) -> ShadowCompareOut:
    divs = await async_compare_partner_payloads(body.legacy, body.remote, SHADOW_KEYS)
    if divs:
        logger.warning("partner_shadow_divergence keys=%s", divs)
    return ShadowCompareOut(divergences=divs)
