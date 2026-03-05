from sqlalchemy import Column, String, Integer, Boolean
# from app.models.base import Base

from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, nullable=True, unique=True, index=True)
    phone = Column(String, nullable=True, unique=True, index=True)
    password_hash = Column(String, nullable=True) # essencial para auth_a1.py
    is_active = Column(Integer, nullable=False, default=1) # ou Boolean