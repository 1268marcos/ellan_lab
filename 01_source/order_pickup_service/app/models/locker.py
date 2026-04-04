# completo (com produtos)
# 01_source/order_pickup_service/app/models/locker.py

from __future__ import annotations

"""
Modelo completo de Lockers com suporte a:
- Multi-região (SP, PT, ES, RJ, + mundo)
- Multi-tenant (operadores terceiros)
- Configuração de slots (P, M, G, XG)
- Compatibilidade com produtos e categorias
- Zonas de temperatura e segurança
"""


from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import (
    Boolean, Column, DateTime, Integer, String, Text, Float, 
    ForeignKey, Enum, BigInteger
)
from sqlalchemy.orm import relationship, validates
from app.core.db import Base
import enum
import json


# ============================================================
# ENUMS COMPARTILHADOS
# ============================================================

class LockerTemperatureZone(str, enum.Enum):
    """Zonas de temperatura suportadas pelos lockers."""
    AMBIENT = "AMBIENT"              # Temperatura ambiente (15-25°C)
    REFRIGERATED = "REFRIGERATED"    # Refrigerado (2-8°C)
    FROZEN = "FROZEN"                # Congelado (-18°C ou menos)
    HEATED = "HEATED"                # Aquecido (para alimentos quentes)
    ANY = "ANY"                      # Aceita qualquer zona (para configs de produto)


class LockerSecurityLevel(str, enum.Enum):
    """Níveis de segurança para itens de valor."""
    STANDARD = "STANDARD"      # Segurança padrão
    ENHANCED = "ENHANCED"      # Câmeras, alarme
    HIGH = "HIGH"              # Cofre, biometria, monitoramento 24h


class OperatorType(str, enum.Enum):
    """Tipos de operadores suportados."""
    LOGISTICS = "LOGISTICS"    # Transportadoras, correios
    ECOMMERCE = "ECOMMERCE"    # Lojas online, marketplaces
    DELIVERY = "DELIVERY"      # Apps de entrega rápida
    PROFESSIONAL = "PROFESSIONAL"  # Profissionais autônomos


class SlotSize(str, enum.Enum):
    """Tamanhos padronizados de gavetas."""
    P = "P"   # Pequeno: 10x10x40cm
    M = "M"   # Médio: 20x20x40cm
    G = "G"   # Grande: 30x40x40cm
    XG = "XG" # Extra Grande: 50x60x40cm


# ============================================================
# MODELO: OPERADOR DE LOCKER (MULTI-TENANT)
# ============================================================

class LockerOperator(Base):
    """
    Cadastro de operadores que podem alugar/gestionar lockers.
    Suporta multi-tenant: logística, e-commerce, profissionais.
    """
    __tablename__ = "locker_operators"

    id = Column(String(64), primary_key=True)  # ex: OP-ELLAN-001
    name = Column(String(128), nullable=False)
    document = Column(String(32), nullable=True, index=True)  # CNPJ/CPF/NIF
    email = Column(String(128), nullable=True)
    phone = Column(String(32), nullable=True)
    
    # Tipo de Operador
    operator_type = Column(String(32), nullable=False, default="LOGISTICS")
    
    # País (ISO 3166-1 alpha-2)
    country = Column(String(2), nullable=False, default="BR")

    # Status e Configurações Comerciais
    active = Column(Boolean, nullable=False, default=True)
    commission_rate = Column(Float, nullable=True)  # % de comissão (ex: 0.01 = 1%)
    currency = Column(String(8), nullable=False, default="BRL")  # BRL, EUR, USD, etc.

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relacionamentos
    lockers = relationship("Locker", back_populates="operator")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "document": self.document,
            "email": self.email,
            "phone": self.phone,
            "operator_type": self.operator_type,
            "country": self.country,
            "active": self.active,
            "commission_rate": self.commission_rate,
            "currency": self.currency,
        }


# ============================================================
# MODELO: CONFIGURAÇÃO DE SLOTS (GAVETAS)
# ============================================================

class LockerSlotConfig(Base):
    """
    Configuração da distribuição de gavetas por tamanho.
    Permite que cada locker tenha uma configuração física única.
    """
    __tablename__ = "locker_slot_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    locker_id = Column(String(64), ForeignKey("lockers.id"), nullable=False, index=True)
    
    # Tamanho da Gaveta
    slot_size = Column(String(8), nullable=False)  # P, M, G, XG
    slot_count = Column(Integer, nullable=False, default=0)  # Total de gavetas deste tamanho
    available_count = Column(Integer, nullable=True)  # Disponível em tempo real (pode ser NULL = usa slot_count)
    
    # Dimensões Físicas (cm)
    width_cm = Column(Integer, nullable=True)
    height_cm = Column(Integer, nullable=True)
    depth_cm = Column(Integer, nullable=True)
    max_weight_kg = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relacionamentos
    locker = relationship("Locker", back_populates="slot_configs")

    def to_dict(self) -> dict:
        return {
            "slot_size": self.slot_size,
            "slot_count": self.slot_count,
            "available_count": self.available_count if self.available_count is not None else self.slot_count,
            "dimensions": {
                "width_cm": self.width_cm,
                "height_cm": self.height_cm,
                "depth_cm": self.depth_cm,
                "max_weight_kg": self.max_weight_kg,
            }
        }


# ============================================================
# MODELO PRINCIPAL: LOCKER
# ============================================================

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
    site_id = Column(String(64), nullable=True, index=True)  # Unidade/Shopping/Filial
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
    slots_count = Column(Integer, nullable=False, default=24)  # Total de slots (soma dos configs)
    machine_id = Column(String(64), nullable=True)  # Hardware/Serial ID do equipamento
    
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
    operator_id = Column(String(64), ForeignKey("locker_operators.id"), nullable=True, index=True)
    tenant_id = Column(String(64), nullable=True, index=True)    # Dono do contrato
    is_rented = Column(Boolean, nullable=False, default=False)   # Se é alugado para terceiro

    # ==================== RETIRADA / TOKEN ====================

    # Instruções de localização física detalhada
    finding_instructions = Column(Text, nullable=True)

    # Tamanho do código de retirada (4 a 12)
    pickup_code_length = Column(Integer, nullable=False, default=6)

    # Política de reutilização do token
    pickup_reuse_policy = Column(String(32), nullable=False, default="NO_REUSE")

    # Janela de reuso (segundos)
    pickup_reuse_window_sec = Column(Integer, nullable=True)

    # Quantidade máxima de reaberturas
    pickup_max_reopens = Column(Integer, nullable=False, default=0)

    # ==================== METADADOS ====================
    metadata_json = Column(Text, nullable=True)  # Configs extras em JSON

    # ==================== TIMESTAMPS ====================
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # ==================== RELACIONAMENTOS ====================
    slot_configs = relationship("LockerSlotConfig", back_populates="locker", cascade="all, delete-orphan")
    product_configs = relationship("ProductLockerConfig", back_populates="locker", cascade="all, delete-orphan")
    operator = relationship("LockerOperator", back_populates="lockers")

    # ==================== MÉTODOS UTILITÁRIOS ====================
    
    def to_dict(self, include_address: bool = True) -> dict:
        """Serializa o locker para JSON/API."""
        result = {
            "id": self.id,
            "external_id": self.external_id,
            "display_name": self.display_name,
            "description": self.description,
            "region": self.region,
            "site_id": self.site_id,
            "timezone": self.timezone,
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
            "allowed_product_categories": [
                pc.to_dict() for pc in self.product_configs if pc.allowed
            ],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "finding_instructions": self.finding_instructions,
            "pickup_config": {
                "code_length": self.pickup_code_length,
                "reuse_policy": self.pickup_reuse_policy,
                "reuse_window_sec": self.pickup_reuse_window_sec,
                "max_reopens": self.pickup_max_reopens,
            },
        }
        
        if include_address:
            result["address"] = {
                "line": self.address_line,
                "number": self.address_number,
                "extra": self.address_extra,
                "district": self.district,
                "city": self.city,
                "state": self.state,
                "postal_code": self.postal_code,
                "country": self.country,
                "latitude": self.latitude,
                "longitude": self.longitude,
            }
        
        return result

    def supports_product(
        self, 
        product_category: str, 
        product_temperature: str = None,
        product_value: int = None
    ) -> tuple[bool, Optional[str]]:
        """
        Verifica se este locker suporta um tipo de produto.
        
        Returns:
            tuple: (allowed: bool, reason: Optional[str])
        """
        # Busca configuração específica para esta categoria
        config = next(
            (c for c in self.product_configs if c.category == product_category), 
            None
        )
        
        if not config or not config.allowed:
            return False, f"Categoria {product_category} não permitida neste locker"
        
        # Verifica compatibilidade de temperatura
        if product_temperature:
            config_temp = config.temperature_zone
            if config_temp != "ANY" and config_temp != product_temperature:
                return False, f"Locker não suporta temperatura {product_temperature} (suporta: {config_temp})"
        
        # Verifica valor máximo
        # if product_value and config.max_value and product_value > config.max_value:
        #    return False, f"Valor R${product_value/100:.2f} excede limite de R${config.max_value/100:.2f}"
        
        return True, None

    def get_total_slots(self) -> int:
        """Calcula o total de slots somando todas as configurações de tamanho."""
        return sum(sc.slot_count for sc in self.slot_configs)

    def get_available_slots(self, size: str = None) -> int:
        """
        Calcula slots disponíveis.
        Se size=None, retorna total geral.
        """
        configs = self.slot_configs
        if size:
            configs = [sc for sc in configs if sc.slot_size == size]
        
        total = 0
        for sc in configs:
            available = sc.available_count if sc.available_count is not None else sc.slot_count
            total += available
        return total

    @validates('temperature_zone')
    def validate_temperature_zone(self, key, value):
        """Valida se o valor é um dos enums suportados."""
        valid_zones = [z.value for z in LockerTemperatureZone]
        if value not in valid_zones:
            raise ValueError(f"Zona de temperatura inválida: {value}. Válidos: {valid_zones}")
        return value

    @validates('security_level')
    def validate_security_level(self, key, value):
        """Valida se o nível de segurança é válido."""
        valid_levels = [l.value for l in LockerSecurityLevel]
        if value not in valid_levels:
            raise ValueError(f"Nível de segurança inválido: {value}. Válidos: {valid_levels}")
        return value