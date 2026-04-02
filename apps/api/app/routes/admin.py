from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import AdminAuditLog, JobRun, User, UserRole, UserSession
from app.services.audit_service import log_admin_action
from app.services.auth_service import get_current_user_role, require_admin, require_super_admin
from app.services.job_service import finish_job, latest_job_by_status, start_job
from app.services.market_service import ingest_regions
from app.services.scheduler_service import run_ingest_cycle, scheduler_state
from app.services.settings_service import get_platform_tracked_regions

router = APIRouter(prefix="/admin", tags=["admin"])

class RoleUpdatePayload(BaseModel):
    role: str

def _pack_job(row):
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

@router.get("")
def admin_index(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    return {"ok": True, "user_id": current_user.id, "role": get_current_user_role(db, current_user.id)}

@router.get("/users")
def admin_users(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    roles = {r.user_id: r.role for r in db.query(UserRole).all()}
    users = db.query(User).order_by(User.id.asc()).all()
    return [
        {
            "id": u.id,
            "handle": u.handle,
            "is_active": u.is_active,
            "role": ("super_admin" if (u.handle or "") == "Varaxian" else roles.get(u.id, "user")),
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]

@router.post("/users/{user_id}/role")
def admin_set_role(user_id: int, payload: RoleUpdatePayload, current_user: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    role = (payload.role or "").strip().lower()
    if role not in {"user", "admin", "super_admin"}:
        raise HTTPException(status_code=400, detail="Invalid role")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if (user.handle or "") == "Varaxian":
        role = "super_admin"
    row = db.query(UserRole).filter(UserRole.user_id == user_id).first()
    if row is None:
        row = UserRole(user_id=user_id, role=role)
        db.add(row)
    else:
        row.role = role
    db.commit()
    db.refresh(row)
    log_admin_action(db, actor_user_id=current_user.id, action="set_user_role", target_type="user", target_id=str(user_id), details={"role": row.role})
    return {"user_id": user_id, "role": row.role}

@router.get("/sessions")
def admin_sessions(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(UserSession).order_by(UserSession.last_seen_at.desc()).limit(100).all()
    users = {u.id: u for u in db.query(User).filter(User.id.in_([r.user_id for r in rows])).all()} if rows else {}
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "handle": users.get(r.user_id).handle if users.get(r.user_id) else None,
            "is_active": r.is_active,
            "expires_at": r.expires_at.isoformat() if r.expires_at else None,
            "last_seen_at": r.last_seen_at.isoformat() if r.last_seen_at else None,
        }
        for r in rows
    ]

@router.get("/scheduler/status")
def admin_scheduler_status(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    latest = db.query(JobRun).order_by(JobRun.started_at.desc()).first()
    latest_success = latest_job_by_status(db, "market_ingest", "success")
    latest_failed = latest_job_by_status(db, "market_ingest", "failed")
    return {
        "scheduler": scheduler_state(),
        "latest_job": _pack_job(latest),
        "latest_successful_market_ingest": _pack_job(latest_success),
        "latest_failed_market_ingest": _pack_job(latest_failed),
    }

@router.post("/scheduler/run")
async def admin_scheduler_run(current_user: User = Depends(require_admin)):
    return await run_ingest_cycle()


@router.get("/audit-logs")
def admin_audit_logs(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(AdminAuditLog).order_by(AdminAuditLog.created_at.desc()).limit(200).all()
    return [
        {
            "id": r.id,
            "actor_user_id": r.actor_user_id,
            "action": r.action,
            "target_type": r.target_type,
            "target_id": r.target_id,
            "details": json.loads(r.details_json) if r.details_json else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]

@router.post("/ingest/run")
async def admin_ingest_run(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    target_regions = get_platform_tracked_regions(db)
    if not target_regions:
        raise HTTPException(status_code=400, detail="No tracked regions configured")
    job = start_job(db, "admin_manual_market_ingest", {"region_ids": target_regions})
    try:
        result = await ingest_regions(db, target_regions)
        finish_job(db, job.id, "success", result)
        log_admin_action(db, actor_user_id=current_user.id, action="manual_ingest_run", target_type="job", target_id=str(job.id), details=result)
        return result
    except Exception as exc:
        finish_job(db, job.id, "failed", {"error": repr(exc)})
        log_admin_action(db, actor_user_id=current_user.id, action="manual_ingest_failed", target_type="job", target_id=str(job.id), details={"error": repr(exc)})
        raise
