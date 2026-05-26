from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.services import bi_efficiency_service

router = APIRouter(prefix="/integration-hub", tags=["integration-hub"])


@router.get("/links")
def integration_links() -> dict:
    s = get_settings()
    return {
        "ml_admin_url": s.ml_admin_url,
        "analytics_service_url": s.analytics_service_url,
        "paths": {
            "ml_dashboard": f"{s.ml_admin_url}/api/v1/ml-admin/dashboard",
            "analytics_financial": f"{s.analytics_service_url}/v1/analytics/financial-dashboard",
            "bi_dashboard": "/api/v1/analytics-bi-admin/dashboard",
            "bi_efficiency": "/api/v1/analytics-bi-admin/efficiency/scorecard",
            "ml_efficiency": f"{s.ml_admin_url}/api/v1/ml-admin/efficiency/scorecard",
        },
    }


@router.get("/health-matrix")
async def health_matrix() -> dict:
    s = get_settings()
    targets = {
        "ml_admin": f"{s.ml_admin_url}/health",
        "analytics_service": f"{s.analytics_service_url}/health",
    }
    out: dict[str, dict] = {}
    async with httpx.AsyncClient(timeout=3.0) as client:
        for name, url in targets.items():
            try:
                r = await client.get(url)
                out[name] = {"url": url, "status": r.status_code, "ok": r.status_code < 400}
            except Exception as exc:
                out[name] = {"url": url, "ok": False, "error": str(exc)}
    return out


@router.get("/unified-efficiency")
def unified_efficiency(db: Session = Depends(get_db)) -> dict:
    bi = bi_efficiency_service.efficiency_scorecard(db)
    pipelines = bi_efficiency_service.list_pipeline_sync(db)
    return {
        "bi": bi,
        "pipelines": pipelines,
        "ml_efficiency_path": f"{get_settings().ml_admin_url}/api/v1/ml-admin/efficiency/scorecard",
    }
