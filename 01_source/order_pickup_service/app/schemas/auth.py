# Rotas de Auth (com Pydantic bem definido)
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, Literal

class RequestOTPIn(BaseModel):
    channel: Literal["EMAIL", "PHONE"]
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, v):
        return v.strip() if v else v

class VerifyOTPIn(BaseModel):
    channel: Literal["EMAIL", "PHONE"]
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    otp_code: str  # "123456"

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


"""
class RegisterIn(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: Optional[str] = None  # A1 usa; A2 pode ignorar

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, v: Optional[str]):
        return v.strip() if v else v

class LoginIn(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: Optional[str] = None  # A1
"""