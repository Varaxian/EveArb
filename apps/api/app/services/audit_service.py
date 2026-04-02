from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.db.models import AdminAuditLog


def log_admin_action(db: Session, *, actor_user_id: int | None, action: str, target_type: str | None = None, target_id: str | None = None, details: dict | None = None) -> AdminAuditLog:
    row = AdminAuditLog(
        actor_user_id=actor_user_id,
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id is not None else None,
        details_json=json.dumps(details or {}),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
