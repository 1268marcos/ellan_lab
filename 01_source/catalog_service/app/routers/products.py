from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.versioning import dto_version_header_value
from app.models.product import Product
from app.schemas.product import BulkProductIn, BulkProductResponse, ProductCreateIn, ProductCreateResponse
from app.schemas.product import ProductVersionOut
from app.services import catalog_service

router = APIRouter(tags=["products"])


def get_redis(request: Request) -> Any:
    return request.app.state.redis_sync


@router.post("/partners/{partner_id}/products", response_model=ProductCreateResponse, status_code=status.HTTP_201_CREATED)
def create_product_route(
    partner_id: str,
    body: ProductCreateIn,
    db: Session = Depends(get_db),
    redis: Any = Depends(get_redis),
) -> ProductCreateResponse:
    try:
        return catalog_service.create_product(db, redis, partner_id, body)
    except catalog_service.CatalogError as e:
        code = str(e)
        if code == "category_not_found":
            raise HTTPException(status_code=404, detail=code)
        if code in ("partner_sku_exists", "invalid_partner"):
            raise HTTPException(status_code=400, detail=code)
        raise HTTPException(status_code=400, detail=code)


@router.post("/products/bulk", response_model=BulkProductResponse)
def bulk_products(
    body: BulkProductIn,
    db: Session = Depends(get_db),
    redis: Any = Depends(get_redis),
) -> BulkProductResponse:
    return catalog_service.bulk_create(db, redis, body)


@router.get("/products/{sku_id}")
def get_product(
    sku_id: str,
    request: Request,
    db: Session = Depends(get_db),
    redis: Any = Depends(get_redis),
):
    r = catalog_service.get_product_detail(db, redis, sku_id)
    if not r:
        raise HTTPException(status_code=404, detail="not_found")
    detail, cache_st = r
    request.state.catalog_cache_status = cache_st
    headers = {"X-DTO-Version": dto_version_header_value()}
    return JSONResponse(content=detail.model_dump(mode="json"), headers=headers)


@router.get("/products/{sku_id}/versions", response_model=list[ProductVersionOut])
def product_versions(sku_id: str, db: Session = Depends(get_db)) -> list[ProductVersionOut]:
    if not db.query(Product).filter(Product.sku_id == sku_id).first():
        raise HTTPException(status_code=404, detail="not_found")
    return catalog_service.list_product_versions(db, sku_id)
