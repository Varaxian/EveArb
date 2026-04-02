from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import JobRun
from app.services.job_service import latest_job_by_status
from app.services.auth_service import require_admin
from app.services.scheduler_service import run_ingest_cycle, scheduler_state
from app.utils.json_utils import safe_json_loads

router = APIRouter(prefix="/scheduler", tags=["scheduler"])

@router.get("/status")
def scheduler_status(db: Session = Depends(get_db), current_user = Depends(require_admin)):
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
            "details": safe_json_loads(row.details_json),
        }

    return {
        "scheduler": scheduler_state(),
        "latest_job": _pack(latest),
        "latest_successful_market_ingest": _pack(latest_success),
        "latest_failed_market_ingest": _pack(latest_failed),
    }

@router.post("/run")
async def scheduler_run_now(current_user = Depends(require_admin)):
    return await run_ingest_cycle()
