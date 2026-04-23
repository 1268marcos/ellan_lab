# 01_source/order_pickup_service/app/models/fiscal_document.py
# 09/04/2026 - CORRIGIDO: Adicionado campo attempt (número de tentativas) para rastrear reimpressões

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON

from app.core.db import Base


class FiscalDocument(Base):
    """
    Simulação / cupom legado no pickup. Novo fluxo canônico: invoices no
    billing_fiscal_service (F-1+); migrar leitores gradualmente.
    """

    __tablename__ = "fiscal_documents"

    __table_args__ = (
        Index("idx_fiscal_order_id", "order_id"),
        Index("idx_fiscal_receipt_code", "receipt_code"),
        Index("idx_fiscal_order_attempt", "order_id", "attempt"),  # NOVO: índice composto para rastrear tentativas
    )

    id = Column(String, primary_key=True)

    order_id = Column(String, nullable=False, unique=False)  # ALTERADO: removido unique=True para permitir múltiplas tentativas

    receipt_code = Column(String(64), nullable=False, unique=True)
    document_type = Column(String(50), nullable=False)

    channel = Column(String(20))
    region = Column(String(10))

    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(10), nullable=False)

    delivery_mode = Column(String(20))
    send_status = Column(String(50))
    send_target = Column(String(255))

    print_status = Column(String(50))
    print_site_path = Column(String(255))

    payload_json = Column(JSON, nullable=False)

    issued_at = Column(DateTime, nullable=False)
    
    # NOVOS CAMPOS PARA CONTROLE DE TENTATIVAS
    attempt = Column(Integer, nullable=False, default=1)  # Número da tentativa (1 = primeira, 2+ = reimpressões)
    previous_receipt_code = Column(String(64), nullable=True)  # Código anterior em caso de reimpressão
    regenerated_at = Column(DateTime, nullable=True)  # Data da última regeneração
    regenerate_reason = Column(String(255), nullable=True)  # Motivo da regeneração

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def is_regenerated(self) -> bool:
        """Verifica se este documento é uma reimpressão (attempt > 1)"""
        return self.attempt > 1

    def get_original_receipt_code(self) -> str | None:
        """Retorna o código original (primeira tentativa)"""
        if self.attempt == 1:
            return self.receipt_code
        return self.previous_receipt_code or self.receipt_code

    def __repr__(self) -> str:
        return (
            f"<FiscalDocument(id={self.id}, order_id={self.order_id}, "
            f"receipt_code={self.receipt_code}, attempt={self.attempt})>"
        )
    
"""
09/04/2026

Principais alterações:
1. Removido unique=True do campo order_id
# Antes
order_id = Column(String, nullable=False, unique=True)
# Depois
order_id = Column(String, nullable=False, unique=False)  # Permite múltiplas tentativas

2. Adicionado índice composto
Index("idx_fiscal_order_attempt", "order_id", "attempt"),  # Para consultas rápidas por ordem + tentativa

3. Novo campo attempt
attempt = Column(Integer, nullable=False, default=1)  # Número da tentativa

4. Novo campo previous_receipt_code
previous_receipt_code = Column(String(64), nullable=True)  # Rastreia o código anterior

5. Novo campo regenerated_at
regenerated_at = Column(DateTime, nullable=True)  # Quando foi regenerado

6. Novo campo regenerate_reason
regenerate_reason = Column(String(255), nullable=True)  # Por que regenerou

7. Métodos auxiliares
def is_regenerated(self) -> bool:
    return self.attempt > 1

def get_original_receipt_code(self) -> str | None:
    if self.attempt == 1:
        return self.receipt_code
    return self.previous_receipt_code or self.receipt_code

    

"""