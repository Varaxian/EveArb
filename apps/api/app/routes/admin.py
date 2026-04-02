from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import JobRun, User, UserRole, UserSession
from app.services.auth_service import get_user_role, require_admin, require_super_admin, set_user_role
from app.services.job_service import latest_job_by_status
from app.services.scheduler_service import restart_scheduler, run_ingest_cycle, scheduler_state

router = APIRouter(prefix="/admin", tags=["admin"])

class UserRolePayload(BaseModel):
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

@router.post('/ingest/run')
async def admin_run_ingest(current_user: User = Depends(require_admin)):
    return await run_ingest_cycle()

@router.get('/scheduler/status')
def admin_scheduler_status(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    latest = db.query(JobRun).order_by(JobRun.started_at.desc()).first()
    latest_success = latest_job_by_status(db, 'market_ingest', 'success')
    latest_failed = latest_job_by_status(db, 'market_ingest', 'failed')
    return {
        'scheduler': scheduler_state(),
        'latest_job': _pack_job(latest),
        'latest_successful_market_ingest': _pack_job(latest_success),
        'latest_failed_market_ingest': _pack_job(latest_failed),
    }

@router.post('/scheduler/restart')
async def admin_scheduler_restart(current_user: User = Depends(require_admin)):
    return {
        'status': 'restarted',
        'scheduler': await restart_scheduler(),
    }

@router.get('/sessions')
def admin_sessions(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(UserSession).order_by(UserSession.last_seen_at.desc()).limit(250).all()
    return [
        {
            'id': row.id,
            'user_id': row.user_id,
            'expires_at': row.expires_at.isoformat() if row.expires_at else None,
            'last_seen_at': row.last_seen_at.isoformat() if row.last_seen_at else None,
            'is_active': row.is_active,
        }
        for row in rows
    ]

@router.get('/users')
def admin_users(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.id.asc()).all()
    role_map = {row.user_id: row.role for row in db.query(UserRole).all()}
    return [
        {
            'id': user.id,
            'handle': user.handle,
            'is_active': user.is_active,
            'role': role_map.get(user.id, 'user'),
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None,
        }
        for user in users
    ]

@router.post('/users/{user_id}/role')
def admin_set_user_role(user_id: int, payload: UserRolePayload, current_user: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    target_user = db.query(User).filter(User.id == user_id).first()
    if target_user is None:
        raise HTTPException(status_code=404, detail='User not found')
    role_row = set_user_role(db, actor_user=current_user, target_user=target_user, role=payload.role)
    return {
        'status': 'updated',
        'user_id': target_user.id,
        'handle': target_user.handle,
        'role': role_row.role,
    }
