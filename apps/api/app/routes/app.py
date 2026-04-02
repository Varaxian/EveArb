from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.services.auth_service import get_current_session, get_current_user, get_user_role, latest_active_token_for_user, latest_characters_for_user

router = APIRouter(prefix="/app", tags=["app"])

@router.get("/me")
def app_me(current_user: User = Depends(get_current_user), current_session = Depends(get_current_session), db: Session = Depends(get_db)):
    characters = latest_characters_for_user(db, current_user.id)
    token = latest_active_token_for_user(db, current_user.id)
    role = get_user_role(db, current_user.id)
    return {
        "user": {
            "id": current_user.id,
            "handle": current_user.handle,
            "is_active": current_user.is_active,
            "role": role,
            "is_admin": role in {"admin", "super_admin"},
        },
        "session": {
            "id": current_session.id,
            "expires_at": current_session.expires_at.isoformat() if current_session.expires_at else None,
            "last_seen_at": current_session.last_seen_at.isoformat() if current_session.last_seen_at else None,
        },
        "characters": [
            {
                "character_id": c.character_id,
                "character_name": c.character_name,
                "scopes": c.scopes,
            }
            for c in characters
        ],
        "token": {
            "present": bool(token),
            "expires_at": token.expires_at.isoformat() if token and token.expires_at else None,
            "has_refresh_token": bool(token and token.refresh_token),
        },
    }
