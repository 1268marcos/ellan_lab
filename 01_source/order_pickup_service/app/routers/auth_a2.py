# (A2 completo)
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import generate_otp_6, hash_otp, create_access_token
from app.schemas.auth import RequestOTPIn, VerifyOTPIn, TokenOut
from app.models.user import User
from app.models.login_otp import LoginOTP, OTPChannel
from app.core.auth_dep import get_current_user

OTP_TTL_SEC = 300          # 5 min
OTP_MAX_ATTEMPTS = 5

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/request-otp")
def request_otp(payload: RequestOTPIn, request: Request, db: Session = Depends(get_db)):
    if payload.channel == "EMAIL" and not payload.email:
        raise HTTPException(status_code=400, detail="email required for EMAIL channel")
    if payload.channel == "PHONE" and not payload.phone:
        raise HTTPException(status_code=400, detail="phone required for PHONE channel")

    # (MVP) Anti-spam simples: recusa se já pediu há <30s
    now = datetime.now(timezone.utc)
    recent_window = now - timedelta(seconds=30)

    q = db.query(LoginOTP).filter(LoginOTP.created_at >= recent_window)
    if payload.channel == "EMAIL":
        q = q.filter(LoginOTP.email == payload.email)
    else:
        q = q.filter(LoginOTP.phone == payload.phone)
    if q.first():
        raise HTTPException(status_code=429, detail="too many requests, wait a bit")

    otp = generate_otp_6()
    otp_row = LoginOTP(
        id=str(uuid.uuid4()),
        channel=OTPChannel.EMAIL if payload.channel == "EMAIL" else OTPChannel.PHONE,
        email=payload.email,
        phone=payload.phone,
        otp_hash=hash_otp(otp),
        expires_at=now + timedelta(seconds=OTP_TTL_SEC),
        requested_ip=request.client.host if request.client else None,
        attempts=0,
    )
    db.add(otp_row)
    db.commit()

    # (MVP) envio “mock”: logar OTP (depois troca por Twilio/Email)
    # IMPORTANTE: em produção real, não retorne o OTP na resposta.
    return {
        "ok": True,
        "channel": payload.channel,
        "expires_in_sec": OTP_TTL_SEC,
        "delivery": "MOCK_LOG_ONLY",
        "debug_otp": otp  # REMOVER em produção
    }

@router.post("/verify-otp", response_model=TokenOut)
def verify_otp(payload: VerifyOTPIn, db: Session = Depends(get_db)):
    if payload.channel == "EMAIL" and not payload.email:
        raise HTTPException(status_code=400, detail="email required")
    if payload.channel == "PHONE" and not payload.phone:
        raise HTTPException(status_code=400, detail="phone required")
    if not payload.otp_code or len(payload.otp_code) != 6 or not payload.otp_code.isdigit():
        raise HTTPException(status_code=400, detail="otp_code must be 6 digits")

    now = datetime.now(timezone.utc)
    otp_hash = hash_otp(payload.otp_code)

    q = db.query(LoginOTP).filter(LoginOTP.used_at.is_(None), LoginOTP.expires_at > now)
    if payload.channel == "EMAIL":
        q = q.filter(LoginOTP.channel == OTPChannel.EMAIL, LoginOTP.email == payload.email)
    else:
        q = q.filter(LoginOTP.channel == OTPChannel.PHONE, LoginOTP.phone == payload.phone)

    otp_row = q.order_by(LoginOTP.created_at.desc()).first()
    if not otp_row:
        raise HTTPException(status_code=401, detail="invalid or expired otp")

    if otp_row.attempts >= OTP_MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="too many attempts")

    if otp_row.otp_hash != otp_hash:
        otp_row.attempts += 1
        db.commit()
        raise HTTPException(status_code=401, detail="invalid otp")

    # marca usado
    otp_row.used_at = now
    db.commit()

    # upsert user
    uq = db.query(User).filter(User.is_active == True)
    if payload.channel == "EMAIL":
        user = uq.filter(User.email == payload.email).first()
        if not user:
            user = User(id=str(uuid.uuid4()), email=payload.email, phone=None, is_active=True)
            db.add(user)
            db.commit()
    else:
        user = uq.filter(User.phone == payload.phone).first()
        if not user:
            user = User(id=str(uuid.uuid4()), email=None, phone=payload.phone, is_active=True)
            db.add(user)
            db.commit()

    token = create_access_token(subject=user.id)
    return TokenOut(access_token=token)

@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "phone": user.phone}

# Para usar Plano de Evolução (Futuro)
"""
Quando quiser migrar para OTP:

Fase 1: Criar tabela login_otps

Fase 2: Implementar serviço de email/SMS real

Fase 3: Adaptar o código OTP para não retornar OTP na resposta

Fase 4: Manter ambos os métodos temporariamente

Fase 5: Depreciar email/senha gradualmente

O sistema OTP do auth.py é mais moderno, mas precisa de mais 
infraestrutura e desenvolvimento. Comece simples e evolua.
"""