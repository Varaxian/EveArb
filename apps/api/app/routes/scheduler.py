from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import JobRun
from app.services.job_service import latest_job_by_status
from app.services.scheduler_service import run_ingest_cycle, scheduler_state

router = APIRouter(prefix="/scheduler", tags=["scheduler"])

@router.get("/status")
def scheduler_status(db: Session = Depends(get_db)):
    latest = db.query(JobRun).order_by(JobRun.started_at.desc()).first()
    latest_success = latest_job_by_status(db, "market_ingest", "success")
    latest_failed = latest_job_by_status(db, "market_ingest", "failed")

    def _pack(row):
        if not row:
            return None
        return {
            "id": row.id,
            "job_name": row.job_name,
            "status": row.status,
            "started_at": row.started_at.isoformat() if row.started_at else None,
            "finished_at": row.finished_at.isoformat() if row.finished_at else None,
            "details": json.loads(row.details_json) if row.details_json else None,
        }

    return {
        "scheduler": scheduler_state(),
        "latest_job": _pack(latest),
        "latest_successful_market_ingest": _pack(latest_success),
        "latest_failed_market_ingest": _pack(latest_failed),
    }

@router.post("/run")
async def scheduler_run_now():
    return await run_ingest_cycle()
