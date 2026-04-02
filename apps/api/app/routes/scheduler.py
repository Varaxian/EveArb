from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import JobRun
from app.services.job_service import latest_job_by_status
from app.services.scheduler_service import run_ingest_cycle, scheduler_state
from app.db.models import User, AdminAuditLog
from app.services.auth_service import require_admin, write_admin_audit_log

router = APIRouter(prefix="/scheduler", tags=["scheduler"])

@router.get("/status")
def scheduler_status(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
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
async def scheduler_run_now(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    write_admin_audit_log(db, actor_user_id=current_user.id, action="run_scheduler_cycle", target_type="scheduler")
    return await run_ingest_cycle()


@router.get("/audit-logs")
def scheduler_audit_logs(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(AdminAuditLog).order_by(AdminAuditLog.created_at.desc()).limit(100).all()
    return [
        {
            "id": row.id,
            "actor_user_id": row.actor_user_id,
            "action": row.action,
            "target_type": row.target_type,
            "target_id": row.target_id,
            "details_json": row.details_json,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]
