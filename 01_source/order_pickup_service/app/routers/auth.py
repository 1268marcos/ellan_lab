# essa rota será substituída
# versão (A1 pronto) - versão futura auth_a2.py (precisa infra)
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.auth import RegisterIn, LoginIn, TokenOut
from app.models.user import User
from app.core.auth_dep import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=TokenOut)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    if not payload.email and not payload.phone:
        raise HTTPException(status_code=400, detail="email or phone is required")

    # A1: senha obrigatória (se você escolher A2 depois, a gente muda isso)
    if not payload.password:
        raise HTTPException(status_code=400, detail="password is required")

    if payload.email and db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="email already exists")
    if payload.phone and db.query(User).filter(User.phone == payload.phone).first():
        raise HTTPException(status_code=409, detail="phone already exists")

    user = User(
        id=str(uuid.uuid4()),
        email=payload.email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        is_active=True,
    )
    db.add(user)
    db.commit()

    token = create_access_token(subject=user.id)
    return TokenOut(access_token=token)

@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    if not payload.email and not payload.phone:
        raise HTTPException(status_code=400, detail="email or phone is required")
    if not payload.password:
        raise HTTPException(status_code=400, detail="password is required")

    q = db.query(User).filter(User.is_active == True)
    if payload.email:
        q = q.filter(User.email == payload.email)
    else:
        q = q.filter(User.phone == payload.phone)

    user = q.first()
    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")

    token = create_access_token(subject=user.id)
    return TokenOut(access_token=token)

@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "phone": user.phone}