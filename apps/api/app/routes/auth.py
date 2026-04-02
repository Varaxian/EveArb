from __future__ import annotations

import secrets

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from app.config import settings
from app.services.esi_auth import build_login_url, exchange_code_for_token, verify_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/login")
async def auth_login():
    if not settings.esi_client_id:
        raise HTTPException(status_code=500, detail="Missing ESI_CLIENT_ID")
    state = secrets.token_urlsafe(24)
    login_url = build_login_url(
        client_id=settings.esi_client_id,
        callback_url=settings.esi_callback_url,
        scopes=settings.esi_scopes,
        state=state,
    )
    return RedirectResponse(url=login_url, status_code=307)

@router.get("/callback")
async def auth_callback(code: str = Query(...), state: str | None = Query(default=None)):
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
    return {
        "status": "authenticated",
        "state": state,
        "character": verify_data,
        "token": {
            "token_type": token_data.get("token_type"),
            "expires_in": token_data.get("expires_in"),
            "refresh_token_present": bool(token_data.get("refresh_token")),
            "scopes": token_data.get("scope"),
        },
    }
