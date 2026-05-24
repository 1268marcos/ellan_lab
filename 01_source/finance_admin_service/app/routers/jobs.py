from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.finance_revenue import JobExecuteOut, JobRunListOut, JobRunOut
from app.services import finance_jobs_service as jobs_svc

router = APIRouter(prefix="/jobs", tags=["scheduled-jobs"])


@router.get("/runs", response_model=JobRunListOut)
def list_job_runs(job_code: str | None = Query(None), db: Session = Depends(get_db)) -> JobRunListOut:
    rows = jobs_svc.list_job_runs(db, job_code)
    items = [JobRunOut.model_validate(r) for r in rows]
    return JobRunListOut(items=items, total=len(items))


@router.post("/run/{job_code}", response_model=JobExecuteOut)
def run_job(job_code: str, db: Session = Depends(get_db)) -> JobExecuteOut:
    result = jobs_svc.run_job(db, job_code)
    return JobExecuteOut(
        job_run_id=result.get("job_run_id", ""),
        job_code=job_code,
        status=result.get("status", "UNKNOWN"),
        recomputed=result.get("recomputed"),
        average_score=result.get("average_score"),
    )


@router.post("/run-all")
def run_all_jobs(db: Session = Depends(get_db)) -> dict:
    results = []
    for code in jobs_svc.JOB_CODES:
        results.append(jobs_svc.run_job(db, code))
    return {"jobs": results}
