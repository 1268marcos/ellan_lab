"""GET /customers/{id}/ltv — LTV preditivo (consentimento ANALYTICS obrigatório por padrão)."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from app.ml_ltv.predict_customer_ltv import predict_customer_ltv_payload
from app.ml_ltv.ltv_data import user_exists

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/customers", tags=["customers-ltv"])


@router.get("/{customer_id}/ltv")
def get_customer_ltv(customer_id: str) -> dict[str, Any]:
    cid = (customer_id or "").strip()
    if not cid:
        raise HTTPException(400, "customer_id inválido")
    if not user_exists(cid):
        raise HTTPException(404, "usuário não encontrado")
    try:
        return predict_customer_ltv_payload(cid, require_consent=True)
    except FileNotFoundError as e:
        logger.warning("ltv bundle missing: %s", e)
        raise HTTPException(503, "modelo LTV não treinado; execute ltv_model_train") from e
    except PermissionError as e:
        raise HTTPException(403, str(e)) from e
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
