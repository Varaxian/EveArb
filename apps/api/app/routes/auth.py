from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import get_db
from app.db.models import User
from app.services.auth_service import (
    SESSION_COOKIE_NAME,
    build_login_url,
    create_user_session,
    exchange_code_for_token,
    get_current_user,
    latest_active_token_for_user,
    latest_characters_for_user,
    refresh_access_token,
    upsert_user_from_esi,
    verify_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/login")
async def auth_login(next_path: str = Query(default="/dashboard")):
    if not settings.esi_client_id:
        raise HTTPException(status_code=500, detail="Missing ESI_CLIENT_ID")
    state = f"{secrets.token_urlsafe(24)}|{next_path}"
    login_url = build_login_url(
        client_id=settings.esi_client_id,
        callback_url=settings.esi_callback_url,
        scopes=settings.esi_scopes,
        state=state,
    )
    return RedirectResponse(url=login_url, status_code=307)

@router.get("/callback")
async def auth_callback(code: str = Query(...), state: str | None = Query(default=None), db: Session = Depends(get_db)):
    if not settings.esi_client_id or not settings.esi_client_secret:
        raise HTTPException(status_code=500, detail="Missing ESI auth configuration")

    token_data = await exchange_code_for_token(
        code=code,
        client_id=settings.esi_client_id,
        client_secret=settings.esi_client_secret,
        callback_url=settings.esi_callback_url,
        user_agent=settings.esi_user_agent,
    )
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=502, detail="ESI token exchange succeeded but returned no access token")

    verify_data = await verify_token(access_token=access_token, user_agent=settings.esi_user_agent)
    user, character, token = upsert_user_from_esi(db, token_data=token_data, verify_data=verify_data)
    session = create_user_session(db, user)

    next_path = "/dashboard"
    if state and "|" in state:
        parts = state.split("|", 1)
        if len(parts) == 2 and parts[1].startswith("/"):
            next_path = parts[1]

    response = RedirectResponse(url=next_path, status_code=302)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session.session_token,
        httponly=True,
        secure=settings.public_base_url.startswith("https://"),
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
        path="/",
    )
    return response

@router.post("/logout")
def auth_logout():
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    return response

@router.get("/sessions")
def auth_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    characters = latest_characters_for_user(db, current_user.id)
    token = latest_active_token_for_user(db, current_user.id)
    return {
        "user_id": current_user.id,
        "handle": current_user.handle,
        "characters": [
            {
                "character_id": c.character_id,
                "character_name": c.character_name,
                "scopes": c.scopes,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            }
            for c in characters
        ],
        "token": {
            "present": bool(token),
            "expires_at": token.expires_at.isoformat() if token and token.expires_at else None,
            "has_refresh_token": bool(token and token.refresh_token),
        },
    }

@router.post("/refresh")
async def auth_refresh(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not settings.esi_client_id or not settings.esi_client_secret:
        raise HTTPException(status_code=500, detail="Missing ESI auth configuration")

    token = latest_active_token_for_user(db, current_user.id)
    if token is None or not token.refresh_token:
        raise HTTPException(status_code=400, detail="No refresh token available")

    token_data = await refresh_access_token(
        refresh_token=token.refresh_token,
        client_id=settings.esi_client_id,
        client_secret=settings.esi_client_secret,
        user_agent=settings.esi_user_agent,
    )
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=502, detail="Refresh succeeded but returned no access token")

    verify_data = await verify_token(access_token=access_token, user_agent=settings.esi_user_agent)
    user, character, token = upsert_user_from_esi(db, token_data=token_data, verify_data=verify_data)

    return {
        "status": "refreshed",
        "user_id": user.id,
        "character_id": character.character_id,
        "expires_at": token.expires_at.isoformat() if token.expires_at else None,
        "has_refresh_token": bool(token.refresh_token),
    }
