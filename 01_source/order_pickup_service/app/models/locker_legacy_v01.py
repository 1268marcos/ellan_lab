# 01_source/order_pickup_service/app/models/locker.py
# completo (com produtos)

from __future__ import annotations

"""
Modelo completo de Lockers com suporte a:
- Multi-região (SP, PT, ES, RJ)
- Multi-tenant (operadores terceiros)
- Configuração de slots (P, M, G, XG)
- Compatibilidade com produtos
- Zonas de temperatura
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.core.db import Base
import enum


class LockerTemperatureZone(str, enum.Enum):
    """Zonas de temperatura suportadas pelos lockers."""
    AMBIENT = "AMBIENT"       # Temperatura ambiente (15-25°C)
    REFRIGERATED = "REFRIGERATED"  # Refrigerado (2-8°C)
    FROZEN = "FROZEN"         # Congelado (-18°C ou menos)
    HEATED = "HEATED"         # Aquecido (para alimentos quentes)


class LockerSecurityLevel(str, enum.Enum):
    """Níveis de segurança para itens de valor."""
    STANDARD = "STANDARD"     # Segurança padrão
    ENHANCED = "ENHANCED"     # Câmeras, alarme
    HIGH = "HIGH"             # Cofre, biometria, monitoramento 24h


class Locker(Base):
    """
    Representa um locker físico ou ponto de retirada (cacifo).
    Fonte única de verdade para existência e configuração operacional.
    """
    __tablename__ = "lockers"

    # ==================== IDENTIFICAÇÃO ====================
    id = Column(String(64), primary_key=True)  # ex: SP-OSASCO-CENTRO-LK-001
    external_id = Column(String(64), nullable=True, index=True)  # ID do operador externo
    display_name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)

    # ==================== LOCALIZAÇÃO E REGIÃO ====================
    region = Column(String(8), nullable=False, index=True)  # SP, PT, ES, RJ
    site_id = Column(String(64), nullable=True, index=True)  # Unidade/Shopping
    timezone = Column(String(64), nullable=False, default="America/Sao_Paulo")

    # ==================== ENDEREÇO COMPLETO ====================
    address_line = Column(String(256), nullable=True)
    address_number = Column(String(32), nullable=True)
    address_extra = Column(String(128), nullable=True)
    district = Column(String(128), nullable=True)
    city = Column(String(128), nullable=True)
    state = Column(String(64), nullable=True)
    postal_code = Column(String(32), nullable=True)
    country = Column(String(64), nullable=False, default="BR")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # ==================== OPERAÇÃO ====================
    active = Column(Boolean, nullable=False, default=True)
    slots_count = Column(Integer, nullable=False, default=24)
    machine_id = Column(String(64), nullable=True)  # Hardware ID
    
    # Configurações de Canal e Pagamento (CSV para flexibilidade)
    allowed_channels = Column(Text, nullable=False, default="ONLINE,KIOSK,APP")
    allowed_payment_methods = Column(Text, nullable=False, default="PIX,CARD,CASH")

    # ==================== TEMPERATURA E SEGURANÇA ====================
    temperature_zone = Column(String(32), nullable=False, default="AMBIENT")
    security_level = Column(String(32), nullable=False, default="STANDARD")
    has_camera = Column(Boolean, nullable=False, default=False)
    has_alarm = Column(Boolean, nullable=False, default=False)
    access_hours = Column(Text, nullable=True)  # ex: "06:00-22:00" ou "24H"

    # ==================== MULTI-TENANT / OPERADOR ====================
    operator_id = Column(String(64), ForeignKey("locker_operators.id"), nullable=True, index=True) # Quem opera este locker
    tenant_id = Column(String(64), nullable=True, index=True)    # Dono do contrato
    is_rented = Column(Boolean, nullable=False, default=False)   # Se é alugado para terceiro

    # ==================== METADADOS ====================
    metadata_json = Column(Text, nullable=True)  # Configs extras em JSON

    # ==================== TIMESTAMPS ====================
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ==================== RELACIONAMENTOS ====================
    slot_configs = relationship("LockerSlotConfig", back_populates="locker", cascade="all, delete-orphan")
    product_configs = relationship("ProductLockerConfig", back_populates="locker", cascade="all, delete-orphan")
    operator = relationship("LockerOperator", back_populates="lockers")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "external_id": self.external_id,
            "display_name": self.display_name,
            "description": self.description,
            "region": self.region,
            "site_id": self.site_id,
            "timezone": self.timezone,
            "address": {
                "line": self.address_line,
                "number": self.address_number,
                "district": self.district,
                "city": self.city,
                "state": self.state,
                "postal_code": self.postal_code,
                "country": self.country,
                "latitude": self.latitude,
                "longitude": self.longitude,
            },
            "active": self.active,
            "slots_count": self.slots_count,
            "allowed_channels": self.allowed_channels.split(",") if self.allowed_channels else [],
            "allowed_payment_methods": self.allowed_payment_methods.split(",") if self.allowed_payment_methods else [],
            "temperature_zone": self.temperature_zone,
            "security_level": self.security_level,
            "has_camera": self.has_camera,
            "has_alarm": self.has_alarm,
            "access_hours": self.access_hours,
            "operator_id": self.operator_id,
            "tenant_id": self.tenant_id,
            "is_rented": self.is_rented,
            "slot_configs": [sc.to_dict() for sc in self.slot_configs],
            "allowed_product_categories": [pc.to_dict() for pc in self.product_configs if pc.allowed],
        }

    def supports_product(self, product_category: str, product_temperature: str = None) -> bool:
        """Verifica se este locker suporta um tipo de produto."""
        for config in self.product_configs:
            if config.category == product_category and config.allowed:
                if product_temperature:
                    if config.temperature_zone == product_temperature or config.temperature_zone == "ANY":
                        return True
                else:
                    return True
        return False


class LockerSlotConfig(Base):
    """
    Configuração da distribuição de gavetas por tamanho (P, M, G, XG).
    Permite que cada locker tenha uma configuração física única.
    """
    __tablename__ = "locker_slot_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    locker_id = Column(String(64), ForeignKey("lockers.id"), nullable=False, index=True)
    
    # Tamanho da Gaveta
    slot_size = Column(String(8), nullable=False)  # P, M, G, XG
    slot_count = Column(Integer, nullable=False, default=0)  # Quantas gavetas deste tamanho
    available_count = Column(Integer, nullable=True)  # Disponível em tempo real
    
    # Dimensões Físicas (cm)
    width_cm = Column(Integer, nullable=True)
    height_cm = Column(Integer, nullable=True)
    depth_cm = Column(Integer, nullable=True)
    max_weight_kg = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    locker = relationship("Locker", back_populates="slot_configs")

    def to_dict(self) -> dict:
        return {
            "slot_size": self.slot_size,
            "slot_count": self.slot_count,
            "available_count": self.available_count or self.slot_count,
            "dimensions": {
                "width_cm": self.width_cm,
                "height_cm": self.height_cm,
                "depth_cm": self.depth_cm,
                "max_weight_kg": self.max_weight_kg,
            }
        }


class LockerOperator(Base):
    """
    Cadastro de operadores que podem alugar lockers.
    Suporta multi-tenant: logística, e-commerce, profissionais autônomos.
    """
    __tablename__ = "locker_operators"

    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    document = Column(String(32), nullable=True, index=True)  # CNPJ/CPF
    email = Column(String(128), nullable=True)
    phone = Column(String(32), nullable=True)
    
    # Tipo de Operador
    operator_type = Column(String(32), nullable=False, default="LOGISTICS")  # LOGISTICS, ECOMMERCE, PROFESSIONAL
    
    # País
    country = Column(String(2), nullable=False, default="BR")  # BR, PT, ES, MX, CO, AR

    # Status
    active = Column(Boolean, nullable=False, default=True)
    
    # Configurações Comerciais
    commission_rate = Column(Float, nullable=True)  # % de comissão
    currency = Column(String(8), nullable=False, default="BRL")

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    lockers = relationship("Locker", back_populates="operator")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "document": self.document,
            "operator_type": self.operator_type,
            "active": self.active,
            "commission_rate": self.commission_rate,
            "currency": self.currency,
        }