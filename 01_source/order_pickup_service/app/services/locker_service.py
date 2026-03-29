# completo (com validação de produtos)
# 01_source/order_pickup_service/app/services/locker_service.py
"""
Serviço completo de validação e consulta de Lockers.
Inclui validação de compatibilidade com produtos.
"""

from __future__ import annotations

from typing import List, Optional, Set, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from app.models.locker import Locker, LockerSlotConfig, LockerOperator
from app.models.product_locker_config import ProductLockerConfig, ProductCategory


def _csv_to_set(value: str | None) -> Set[str]:
    """Converte CSV string em set para validação rápida."""
    if not value:
        return set()
    return {item.strip().upper() for item in str(value).split(",") if item.strip()}


def get_locker_or_404(db: Session, locker_id: str) -> Locker:
    """Busca locker e lança 400 se não existir."""
    locker = (
        db.query(Locker)
        .options(
            joinedload(Locker.slot_configs),
            joinedload(Locker.product_configs)
        )
        .filter(Locker.id == locker_id)
        .first()
    )

    if not locker:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "type": "LOCKER_NOT_FOUND",
                "message": f"Locker não encontrado: {locker_id}",
                "locker_id": locker_id,
                "retryable": False,
            },
        )
    return locker


def validate_locker_for_order(
    *,
    db: Session,
    locker_id: str,
    region: str,
    channel: str = "ONLINE",
    payment_method: str = "PIX",
    product_category: Optional[str] = None,
    product_value: Optional[float] = None,
    product_weight_kg: Optional[float] = None,
    product_dimensions: Optional[Dict[str, int]] = None,
) -> Locker:
    """
    Validações completas para criação de pedido com retirada em locker.
    Inclui validação de compatibilidade com produtos.
    """
    locker = get_locker_or_404(db, locker_id)

    # 1. Locker Ativo?
    if not locker.active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "LOCKER_INACTIVE",
                "message": f"Locker {locker_id} está inativo",
                "locker_id": locker_id,
                "retryable": False,
            },
        )

    # 2. Região Correta?
    if str(locker.region).upper() != str(region).upper():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "LOCKER_REGION_MISMATCH",
                "message": f"Locker {locker_id} não pertence à região {region}",
                "locker_id": locker_id,
                "locker_region": locker.region,
                "payload_region": region,
                "retryable": False,
            },
        )

    # 3. Canal Permitido?
    allowed_channels = _csv_to_set(locker.allowed_channels)
    if allowed_channels and channel.upper() not in allowed_channels:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "LOCKER_CHANNEL_NOT_ALLOWED",
                "message": f"Locker {locker_id} não aceita canal {channel}",
                "locker_id": locker_id,
                "allowed_channels": list(allowed_channels),
                "retryable": False,
            },
        )

    # 4. Método de Pagamento Permitido?
    allowed_methods = _csv_to_set(locker.allowed_payment_methods)
    if allowed_methods and payment_method.upper() not in allowed_methods:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "LOCKER_PAYMENT_METHOD_NOT_ALLOWED",
                "message": f"Método {payment_method} não permitido em {locker_id}",
                "locker_id": locker_id,
                "allowed_methods": list(allowed_methods),
                "retryable": False,
            },
        )

    # 5. Slots Configurados?
    if not locker.slot_configs or sum(sc.slot_count for sc in locker.slot_configs) == 0:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "type": "LOCKER_NO_SLOT_CONFIG",
                "message": f"Locker {locker_id} sem configuração de gavetas",
                "locker_id": locker_id,
                "retryable": False,
            },
        )

    # 6. Compatibilidade com Produto (NOVO)
    if product_category:
        validate_product_compatibility(
            locker=locker,
            product_category=product_category,
            product_value=product_value,
            product_weight_kg=product_weight_kg,
            product_dimensions=product_dimensions,
        )

    return locker


def validate_product_compatibility(
    *,
    locker: Locker,
    product_category: str,
    product_value: Optional[float] = None,
    product_weight_kg: Optional[float] = None,
    product_dimensions: Optional[Dict[str, int]] = None,
):
    """
    Valida se o produto é compatível com o locker.
    """
    # Busca configuração para esta categoria
    product_config = None
    for config in locker.product_configs:
        if config.category == product_category.upper() and config.allowed:
            product_config = config
            break
    
    if not product_config:
        # Verifica se há uma configuração explícita negando esta categoria
        for config in locker.product_configs:
            if config.category == product_category.upper() and not config.allowed:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "type": "PRODUCT_CATEGORY_NOT_ALLOWED",
                        "message": f"Categoria {product_category} não permitida em {locker.id}",
                        "locker_id": locker.id,
                        "product_category": product_category,
                        "retryable": False,
                    },
                )
        
        # Se não há configuração, assume que é permitido (fallback)
        return

    # Valida Valor
    if product_value is not None:
        if product_config.min_value is not None and product_value < product_config.min_value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "type": "PRODUCT_VALUE_TOO_LOW",
                    "message": f"Valor do produto abaixo do mínimo para {locker.id}",
                    "locker_id": locker.id,
                    "product_value": product_value,
                    "min_value": product_config.min_value,
                    "retryable": False,
                },
            )
        if product_config.max_value is not None and product_value > product_config.max_value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "type": "PRODUCT_VALUE_TOO_HIGH",
                    "message": f"Valor do produto acima do máximo para {locker.id}",
                    "locker_id": locker.id,
                    "product_value": product_value,
                    "max_value": product_config.max_value,
                    "retryable": False,
                },
            )

    # Valida Peso
    if product_weight_kg is not None and product_config.max_weight_kg is not None:
        if product_weight_kg > product_config.max_weight_kg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "type": "PRODUCT_WEIGHT_EXCEEDED",
                    "message": f"Peso do produto excede limite em {locker.id}",
                    "locker_id": locker.id,
                    "product_weight_kg": product_weight_kg,
                    "max_weight_kg": product_config.max_weight_kg,
                    "retryable": False,
                },
            )

    # Valida Dimensões
    if product_dimensions and product_config.max_dimensions:
        if product_config.max_width_cm and product_dimensions.get("width", 0) > product_config.max_width_cm:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "type": "PRODUCT_DIMENSION_EXCEEDED",
                    "message": f"Largura do produto excede limite em {locker.id}",
                    "locker_id": locker.id,
                    "retryable": False,
                },
            )
        if product_config.max_height_cm and product_dimensions.get("height", 0) > product_config.max_height_cm:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "type": "PRODUCT_DIMENSION_EXCEEDED",
                    "message": f"Altura do produto excede limite em {locker.id}",
                    "locker_id": locker.id,
                    "retryable": False,
                },
            )
        if product_config.max_depth_cm and product_dimensions.get("depth", 0) > product_config.max_depth_cm:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "type": "PRODUCT_DIMENSION_EXCEEDED",
                    "message": f"Profundidade do produto excede limite em {locker.id}",
                    "locker_id": locker.id,
                    "retryable": False,
                },
            )

    # Valida Temperatura
    if locker.temperature_zone != "AMBIENT":
        if product_config.temperature_zone != "ANY" and product_config.temperature_zone != locker.temperature_zone:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "type": "PRODUCT_TEMPERATURE_MISMATCH",
                    "message": f"Produto requer zona térmica diferente em {locker.id}",
                    "locker_id": locker.id,
                    "locker_temperature": locker.temperature_zone,
                    "product_temperature": product_config.temperature_zone,
                    "retryable": False,
                },
            )


def get_available_lockers_by_region(
    db: Session,
    region: str,
    active_only: bool = True,
    product_category: Optional[str] = None,
) -> List[Locker]:
    """Lista lockers disponíveis para uma região, opcionalmente filtrando por categoria de produto."""
    query = db.query(Locker).filter(Locker.region == region.upper())
    if active_only:
        query = query.filter(Locker.active == True)
    
    lockers = query.order_by(Locker.display_name).all()
    
    # Filtra por compatibilidade com produto se especificado
    if product_category:
        lockers = [
            locker for locker in lockers 
            if locker.supports_product(product_category)
        ]
    
    return lockers


def get_locker_slot_summary(locker: Locker) -> dict:
    """Retorna resumo de slots por tamanho."""
    summary = {"P": 0, "M": 0, "G": 0, "XG": 0, "total": 0}
    for config in locker.slot_configs:
        if config.slot_size in summary:
            summary[config.slot_size] = config.slot_count
        summary["total"] += config.slot_count
    return summary


def get_compatible_lockers_for_product(
    db: Session,
    region: str,
    product_category: str,
    product_value: Optional[float] = None,
    product_weight_kg: Optional[float] = None,
) -> List[Locker]:
    """
    Encontra todos os lockers compatíveis com um produto específico.
    Usado no checkout para mostrar opções de retirada.
    """
    lockers = get_available_lockers_by_region(db, region, active_only=True)
    compatible = []
    
    for locker in lockers:
        try:
            validate_product_compatibility(
                locker=locker,
                product_category=product_category,
                product_value=product_value,
                product_weight_kg=product_weight_kg,
            )
            compatible.append(locker)
        except HTTPException:
            continue
    
    return compatible