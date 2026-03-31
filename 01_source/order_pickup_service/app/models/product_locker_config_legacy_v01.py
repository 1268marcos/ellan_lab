# novo (compatibilidade)
# 01_source/order_pickup_service/app/models/product_locker_config.py

from __future__ import annotations

"""
Configuração de compatibilidade entre Produtos e Lockers.
Define quais categorias de produtos podem ser armazenadas em cada locker.
"""


from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.core.db import Base


class ProductLockerConfig(Base):
    """
    Define regras de compatibilidade entre categorias de produtos e lockers.
    Um locker pode aceitar ou rejeitar categorias específicas.
    """
    __tablename__ = "product_locker_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    locker_id = Column(String(64), ForeignKey("lockers.id"), nullable=False, index=True)
    
    # Categoria do Produto
    category = Column(String(64), nullable=False, index=True)  # ex: ELECTRONICS, FOOD, DOCUMENTS
    subcategory = Column(String(64), nullable=True)  # ex: SMARTPHONE, PERISHABLE, LEGAL
    
    # Permissão
    allowed = Column(Boolean, nullable=False, default=True)  # Se esta categoria é permitida
    
    # Restrições de Temperatura
    temperature_zone = Column(String(32), nullable=False, default="ANY")  # ANY, AMBIENT, REFRIGERATED, FROZEN
    
    # Restrições de Valor
    min_value = Column(Float, nullable=True)  # Valor mínimo do produto (centavos)
    max_value = Column(Float, nullable=True)  # Valor máximo do produto (centavos)
    
    # Restrições de Peso
    max_weight_kg = Column(Float, nullable=True)  # Peso máximo permitido
    
    # Restrições de Dimensões
    max_width_cm = Column(Integer, nullable=True)
    max_height_cm = Column(Integer, nullable=True)
    max_depth_cm = Column(Integer, nullable=True)
    
    # Restrições Especiais
    requires_signature = Column(Boolean, nullable=False, default=False)  # Precisa de assinatura na retirada
    requires_id = Column(Boolean, nullable=False, default=False)  # Precisa de documento na retirada
    is_fragile = Column(Boolean, nullable=False, default=False)  # Produto frágil
    is_hazardous = Column(Boolean, nullable=False, default=False)  # Produto perigoso (proibido na maioria)
    
    # Prioridade de Alocação
    priority = Column(Integer, nullable=False, default=100)  # Menor = maior prioridade
    
    # Observações
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    locker = relationship("Locker", back_populates="product_configs")

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "subcategory": self.subcategory,
            "allowed": self.allowed,
            "temperature_zone": self.temperature_zone,
            "value_range": {
                "min": self.min_value,
                "max": self.max_value,
            },
            "max_weight_kg": self.max_weight_kg,
            "max_dimensions": {
                "width_cm": self.max_width_cm,
                "height_cm": self.max_height_cm,
                "depth_cm": self.max_depth_cm,
            },
            "requirements": {
                "requires_signature": self.requires_signature,
                "requires_id": self.requires_id,
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

    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    parent_category = Column(String(64), nullable=True, index=True)  # Para hierarquia
    
    # Configurações Padrão
    default_temperature_zone = Column(String(32), nullable=False, default="AMBIENT")
    default_security_level = Column(String(32), nullable=False, default="STANDARD")
    is_hazardous = Column(Boolean, nullable=False, default=False)
    requires_age_verification = Column(Boolean, nullable=False, default=False)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "parent_category": self.parent_category,
            "default_temperature_zone": self.default_temperature_zone,
            "default_security_level": self.default_security_level,
            "is_hazardous": self.is_hazardous,
            "requires_age_verification": self.requires_age_verification,
        }