# 01_source/order_pickup_service/app/models/product_locker_config.py
"""
Configuração de compatibilidade entre Produtos e Lockers.
Define quais categorias de produtos podem ser armazenadas em cada locker.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Boolean, Column, DateTime, Integer, String, Text, 
    Float, ForeignKey, BigInteger, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.core.db import Base


class ProductLockerConfig(Base):
    """
    Define regras de compatibilidade entre categorias de produtos e lockers.
    Um locker pode aceitar ou rejeitar categorias específicas com overrides.
    """
    __tablename__ = "product_locker_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Chaves estrangeiras
    locker_id = Column(String(64), ForeignKey("lockers.id"), nullable=False, index=True)
    category = Column(String(64), ForeignKey("product_categories.id"), nullable=False, index=True)
    
    # ==================== PERMISSÃO ====================
    allowed = Column(Boolean, nullable=False, default=True)
    
    # ==================== TEMPERATURA ====================
    temperature_zone = Column(String(32), nullable=False, default="ANY")  # ANY, AMBIENT, REFRIGERATED, FROZEN
    
    # ==================== VALOR (em centavos) ====================
    # Usando BigInteger para suportar valores altos em centavos (ex: R$ 10.000,00 = 1000000)
    min_value = Column(BigInteger, nullable=True)
    # max_value = Column(BigInteger, nullable=True)
    
    # ==================== PESO E DIMENSÕES ====================
    max_weight_kg = Column(Float, nullable=True)
    max_width_cm = Column(Integer, nullable=True)
    max_height_cm = Column(Integer, nullable=True)
    max_depth_cm = Column(Integer, nullable=True)
    
    # ==================== REQUISITOS ESPECIAIS ====================
    # requires_signature = Column(Boolean, nullable=False, default=False)
    # requires_id = Column(Boolean, nullable=False, default=False)
    # requires_age_verification = Column(Boolean, nullable=False, default=False)
    
    # ==================== CLASSIFICAÇÃO ====================
    is_fragile = Column(Boolean, nullable=False, default=False)
    is_hazardous = Column(Boolean, nullable=False, default=False)
    priority = Column(Integer, nullable=False, default=100)  # Menor = maior prioridade
    
    # ==================== METADADOS ====================
    notes = Column(Text, nullable=True)
    
    # ==================== TIMESTAMPS (timezone-aware para PostgreSQL) ====================
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # ==================== RELACIONAMENTOS ====================
    locker = relationship("Locker", back_populates="product_configs")
    category_ref = relationship("ProductCategory", back_populates="product_locker_configs")

    __table_args__ = (
        # Garante unicidade: uma categoria só pode ter uma configuração por locker
        UniqueConstraint('locker_id', 'category', name='uq_locker_category'),
    )

    def to_dict(self) -> dict:
        return {
            "locker_id": self.locker_id,
            "category": self.category,
            "allowed": self.allowed,
            "temperature_zone": self.temperature_zone,
            "value_range": {
                "min": self.min_value,
                # "max": self.max_value,
            },
            "max_weight_kg": self.max_weight_kg,
            "max_dimensions": {
                "width_cm": self.max_width_cm,
                "height_cm": self.max_height_cm,
                "depth_cm": self.max_depth_cm,
            },
            "requirements": {
                # "requires_signature": self.requires_signature,
                # "requires_id": self.requires_id,
                # "requires_age_verification": self.requires_age_verification,
                "is_fragile": self.is_fragile,
                "is_hazardous": self.is_hazardous,
            },
            "priority": self.priority,
            "notes": self.notes,
        }


class ProductCategory(Base):
    """
    Catálogo mestre de categorias de produtos suportadas pela plataforma.
    Usado para padronizar as categorias em todos os lockers.
    """
    __tablename__ = "product_categories"

    # ==================== IDENTIFICAÇÃO ====================
    id = Column(String(64), primary_key=True)  # ex: ELECTRONICS, PHARMACY_OTC_MEDS
    name = Column(String(128), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Hierarquia opcional
    parent_category = Column(String(64), nullable=True, index=True)
    
    # ==================== CONFIGURAÇÕES PADRÃO ====================
    default_temperature_zone = Column(String(32), nullable=False, default="AMBIENT")
    default_security_level = Column(String(32), nullable=False, default="STANDARD")
    
    # ==================== RESTRIÇÕES GLOBAIS ====================
    is_hazardous = Column(Boolean, nullable=False, default=False)
    
    # Requisitos de verificação (APENAS os que existem no DB)
    # requires_age_verification = Column(Boolean, nullable=False, default=False)
    
    # ==================== TIMESTAMPS ====================
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # ==================== RELACIONAMENTOS ====================
    product_locker_configs = relationship(
        "ProductLockerConfig", 
        back_populates="category_ref", 
        cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "parent_category": self.parent_category,
            "default_temperature_zone": self.default_temperature_zone,
            "default_security_level": self.default_security_level,
            "is_hazardous": self.is_hazardous,
            # "requires_age_verification": self.requires_age_verification,
        }