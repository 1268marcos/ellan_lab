from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.partner import Partner, PartnerApiKey

router = APIRouter(tags=["auth"])


class LoginRequest(BaseModel):
    partner_id: UUID
    api_key: str


class PartnerPayload(BaseModel):
    id: str
    name: str
    role: str


class LoginResponse(BaseModel):
    token: str
    partner: PartnerPayload


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _encode_jwt(payload: dict[str, object], secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _b64url(json.dumps(header, separators=(",", ":"), sort_keys=True).encode())
    payload_b64 = _b64url(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    signing_input = f"{header_b64}.{payload_b64}".encode()
    signature = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    return f"{header_b64}.{payload_b64}.{_b64url(signature)}"


def _hash_api_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


@router.post("/v1/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    partner = db.query(Partner).filter(Partner.id == str(body.partner_id)).first()
    if not partner:
        raise HTTPException(status_code=401, detail="invalid credentials")

    hashed = _hash_api_key(body.api_key)
    api_key = (
        db.query(PartnerApiKey)
        .filter(
            PartnerApiKey.partner_id == partner.id,
            PartnerApiKey.key_hash == hashed,
            PartnerApiKey.is_active.is_(True),
        )
        .first()
    )
    if not api_key:
        raise HTTPException(status_code=401, detail="invalid credentials")

    now = int(time.time())
    secret = os.getenv("PARTNER_JWT_SECRET", "partner-service-dev-secret")
    exp_seconds = int(os.getenv("PARTNER_JWT_EXP_SECONDS", "3600"))
    token = _encode_jwt(
        {
            "sub": partner.id,
            "partner_id": partner.id,
            "name": partner.name,
            "role": "partner",
            "iat": now,
            "exp": now + exp_seconds,
        },
        secret,
    )
    return LoginResponse(
        token=token,
        partner=PartnerPayload(id=partner.id, name=partner.name, role="partner"),
    )
