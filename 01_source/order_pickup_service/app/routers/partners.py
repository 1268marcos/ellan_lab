from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.internal_auth import require_internal_token
from app.services import partner_client
from app.workers.consistency_checker import compare_schemas

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["partners"])
internal_router = APIRouter(prefix="/internal/partners", tags=["partners-shadow"])

SHADOW_KEYS = ("id", "name", "partner_type", "legal_name", "contact_email", "status")


class ShadowCompareIn(BaseModel):
    legacy: dict[str, Any] = Field(default_factory=dict)
    remote: dict[str, Any] = Field(default_factory=dict)


class ShadowCompareOut(BaseModel):
    divergences: list[str]


async def async_compare_partner_payloads(
    legacy: dict[str, Any],
    remote: dict[str, Any],
    keys: tuple[str, ...] = SHADOW_KEYS,
) -> list[str]:
    return await asyncio.to_thread(compare_schemas, legacy, remote, keys)


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


@internal_router.post("/shadow-compare", response_model=ShadowCompareOut)
async def shadow_compare(
    body: ShadowCompareIn,
    _: bool = Depends(require_internal_token),
) -> ShadowCompareOut:
    divs = await async_compare_partner_payloads(body.legacy, body.remote, SHADOW_KEYS)
    if divs:
        logger.warning("partner_shadow_divergence keys=%s", divs)
    return ShadowCompareOut(divergences=divs)
