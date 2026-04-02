from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.services.auth_service import get_current_session, get_current_user, latest_active_token_for_user, latest_characters_for_user
from app.services.settings_service import get_platform_tracked_regions
from app.services.region_name_service import resolve_region_names
from app.config import settings

router = APIRouter(prefix="/app", tags=["app"])

@router.get("/me")
def app_me(current_user: User = Depends(get_current_user), current_session = Depends(get_current_session), db: Session = Depends(get_db)):
    characters = latest_characters_for_user(db, current_user.id)
    token = latest_active_token_for_user(db, current_user.id)
    return {
        "user": {
            "id": current_user.id,
            "handle": current_user.handle,
            "is_active": current_user.is_active,
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

@router.get("/region-options")
async def region_options(db: Session = Depends(get_db)):
    region_ids = get_platform_tracked_regions(db)
    names = await resolve_region_names(region_ids, settings.esi_user_agent)
    return [
        {"region_id": rid, "region_name": names.get(rid, str(rid))}
        for rid in region_ids
    ]
