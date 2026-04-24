# novo (CRUD de lockers)
# 01_source/order_pickup_service/app/routers/locker.py

from __future__ import annotations

"""
Router para gestão de Lockers (CRUD administrativo).
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.locker import Locker, LockerOperator
from app.models.product_locker_config import ProductLockerConfig, ProductCategory
from app.services.locker_service import (
    get_locker_or_404,
    get_available_lockers_by_region,
    get_compatible_lockers_for_product,
)
from app.schemas.locker import (
    LockerCreateSchema,
    LockerUpdateSchema,
    LockerResponseSchema,
    LockerListResponseSchema,
    LockerOperatorCreateSchema,
    LockerOperatorResponseSchema,
    ProductCategoryCreateSchema,
    ProductCategoryResponseSchema,
)

router = APIRouter(prefix="/lockers", tags=["lockers"])


# ==================== LOCKERS ====================
@router.get("", response_model=LockerListResponseSchema)
def list_lockers(
    region: Optional[str] = Query(None, description="Filtrar por região (SP, PT, ES, RJ)"),
    active_only: bool = Query(True, description="Apenas lockers ativos"),
    product_category: Optional[str] = Query(None, description="Filtrar por compatibilidade com produto"),
    db: Session = Depends(get_db),
):
    """Lista lockers disponíveis com filtros opcionais."""
    lockers = get_available_lockers_by_region(
        db=db,
        region=region or "SP",
        active_only=active_only,
        product_category=product_category,
    )
    return LockerListResponseSchema(
        lockers=[LockerResponseSchema.model_validate(l) for l in lockers],
        total=len(lockers),
        region=region,
    )


@router.get("/compatible", response_model=LockerListResponseSchema)
def list_compatible_lockers(
    region: str = Query(..., description="Região obrigatória"),
    product_category: str = Query(..., description="Categoria do produto"),
    product_value: Optional[float] = Query(None, description="Valor do produto em centavos"),
    product_weight_kg: Optional[float] = Query(None, description="Peso do produto em kg"),
    db: Session = Depends(get_db),
):
    """Lista apenas lockers compatíveis com um produto específico."""
    lockers = get_compatible_lockers_for_product(
        db=db,
        region=region,
        product_category=product_category,
        product_value=product_value,
        product_weight_kg=product_weight_kg,
    )
    return LockerListResponseSchema(
        lockers=[LockerResponseSchema.model_validate(l) for l in lockers],
        total=len(lockers),
        region=region,
    )


@router.get("/{locker_id}", response_model=LockerResponseSchema)
def get_locker(locker_id: str, db: Session = Depends(get_db)):
    """Obtém detalhes completos de um locker."""
    locker = get_locker_or_404(db, locker_id)
    return LockerResponseSchema.model_validate(locker)


@router.post("", response_model=LockerResponseSchema, status_code=status.HTTP_201_CREATED)
def create_locker(locker_data: LockerCreateSchema, db: Session = Depends(get_db)):
    """Cria um novo locker com configuração completa."""
    # Verifica se já existe
    existing = db.query(Locker).filter(Locker.id == locker_data.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": "LOCKER_ALREADY_EXISTS", "message": f"Locker {locker_data.id} já existe"},
        )
    
    # Cria locker
    address = locker_data.address.dict() if locker_data.address else {}
    locker = Locker(
        id=locker_data.id,
        external_id=locker_data.external_id,
        display_name=locker_data.display_name,
        description=locker_data.description,
        region=locker_data.region,
        site_id=locker_data.site_id,
        timezone=locker_data.timezone,
        address_line=address.get("line"),
        address_number=address.get("number"),
        address_extra=address.get("extra"),
        district=address.get("district"),
        city=address.get("city"),
        state=address.get("state"),
        postal_code=address.get("postal_code"),
        country=address.get("country", "BR"),
        latitude=address.get("latitude"),
        longitude=address.get("longitude"),
        active=locker_data.active,
        slots_count=locker_data.slots_count,
        temperature_zone=locker_data.temperature_zone,
        security_level=locker_data.security_level,
        has_camera=locker_data.has_camera,
        has_alarm=locker_data.has_alarm,
        access_hours=locker_data.access_hours,
        operator_id=locker_data.operator_id,
        tenant_id=locker_data.tenant_id,
        is_rented=locker_data.is_rented,
        allowed_channels=locker_data.allowed_channels,
        allowed_payment_methods=locker_data.allowed_payment_methods,
    )
    db.add(locker)
    db.flush()
    
    # Cria slot configs
    if locker_data.slot_configs:
        for slot in locker_data.slot_configs:
            slot_config = LockerSlotConfig(
                locker_id=locker.id,
                slot_size=slot.slot_size,
                slot_count=slot.slot_count,
                width_mm=slot.dimensions.width_mm if slot.dimensions else None,
                height_mm=slot.dimensions.height_mm if slot.dimensions else None,
                depth_mm=slot.dimensions.depth_mm if slot.dimensions else None,
                max_weight_g=slot.dimensions.max_weight_g if slot.dimensions else None,
            )
            db.add(slot_config)
    
    def _cm_to_mm(v):
        if v is None:
            return None
        return int(round(float(v) * 10))

    def _kg_to_g(v):
        if v is None:
            return None
        return int(round(float(v) * 1000))

    # Cria product configs (API em cm/kg → persistência mm/g)
    if locker_data.product_configs:
        for prod in locker_data.product_configs:
            md = prod.max_dimensions or {}
            product_config = ProductLockerConfig(
                locker_id=locker.id,
                category=prod.category,
                allowed=prod.allowed,
                temperature_zone=prod.temperature_zone,
                min_value=int(prod.value_range["min"]) if prod.value_range and prod.value_range.get("min") is not None else None,
                max_weight_g=_kg_to_g(prod.max_weight_kg),
                max_width_mm=_cm_to_mm(md.get("width")),
                max_height_mm=_cm_to_mm(md.get("height")),
                max_depth_mm=_cm_to_mm(md.get("depth")),
                is_fragile=prod.requirements.is_fragile if prod.requirements else False,
                is_hazardous=prod.requirements.is_hazardous if prod.requirements else False,
                priority=prod.priority,
                notes=prod.notes,
            )
            db.add(product_config)
    
    db.commit()
    db.refresh(locker)
    return LockerResponseSchema.model_validate(locker)


@router.patch("/{locker_id}", response_model=LockerResponseSchema)
def update_locker(locker_id: str, locker_data: LockerUpdateSchema, db: Session = Depends(get_db)):
    """Atualiza configurações de um locker existente."""
    locker = get_locker_or_404(db, locker_id)
    
    update_data = locker_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(locker, field, value)
    
    db.commit()
    db.refresh(locker)
    return LockerResponseSchema.model_validate(locker)


@router.delete("/{locker_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_locker(locker_id: str, db: Session = Depends(get_db)):
    """Remove um locker (apenas se não houver pedidos ativos)."""
    locker = get_locker_or_404(db, locker_id)
    
    # Verifica se há pedidos ativos
    from app.models.order import Order
    active_orders = db.query(Order).filter(
        Order.locker_id == locker_id,
        Order.status.in_(["PENDING", "PAID", "READY_FOR_PICKUP"])
    ).count()
    
    if active_orders > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "LOCKER_HAS_ACTIVE_ORDERS",
                "message": f"Locker {locker_id} possui {active_orders} pedidos ativos",
                "active_orders": active_orders,
            },
        )
    
    db.delete(locker)
    db.commit()


# ==================== OPERATORS ====================
@router.get("/operators", response_model=List[LockerOperatorResponseSchema])
def list_operators(db: Session = Depends(get_db)):
    """Lista todos os operadores de lockers."""
    operators = db.query(LockerOperator).all()
    return [LockerOperatorResponseSchema.model_validate(o) for o in operators]


@router.post("/operators", response_model=LockerOperatorResponseSchema, status_code=status.HTTP_201_CREATED)
def create_operator(operator_data: LockerOperatorCreateSchema, db: Session = Depends(get_db)):
    """Cria um novo operador."""
    existing = db.query(LockerOperator).filter(LockerOperator.id == operator_data.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": "OPERATOR_ALREADY_EXISTS", "message": f"Operador {operator_data.id} já existe"},
        )
    
    operator = LockerOperator(**operator_data.dict())
    db.add(operator)
    db.commit()
    db.refresh(operator)
    return LockerOperatorResponseSchema.model_validate(operator)


# ==================== PRODUCT CATEGORIES ====================
@router.get("/product-categories", response_model=List[ProductCategoryResponseSchema])
def list_product_categories(db: Session = Depends(get_db)):
    """Lista todas as categorias de produtos suportadas."""
    categories = db.query(ProductCategory).all()
    return [ProductCategoryResponseSchema.model_validate(c) for c in categories]


@router.post("/product-categories", response_model=ProductCategoryResponseSchema, status_code=status.HTTP_201_CREATED)
def create_product_category(category_data: ProductCategoryCreateSchema, db: Session = Depends(get_db)):
    """Cria uma nova categoria de produto."""
    existing = db.query(ProductCategory).filter(ProductCategory.id == category_data.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": "CATEGORY_ALREADY_EXISTS", "message": f"Categoria {category_data.id} já existe"},
        )
    
    category = ProductCategory(**category_data.dict())
    db.add(category)
    db.commit()
    db.refresh(category)
    return ProductCategoryResponseSchema.model_validate(category)