import enum
from sqlalchemy import Column, String, DateTime, Integer, Enum, Index
from datetime import datetime
from app.models.base import Base

class OTPChannel(str, enum.Enum):
    EMAIL = "EMAIL"
    PHONE = "PHONE"

class LoginOTP(Base):
    __tablename__ = "login_otps"

    id = Column(String, primary_key=True)
    channel = Column(Enum(OTPChannel), nullable=False)

    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    otp_hash = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)

    attempts = Column(Integer, nullable=False, default=0)
    requested_ip = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_login_otps_email", "email"),
        Index("ix_login_otps_phone", "phone"),
        Index("ix_login_otps_expires_at", "expires_at"),
    )