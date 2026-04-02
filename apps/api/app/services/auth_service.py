from __future__ import annotations

import base64
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import get_db
from app.db.models import EveAuthToken, EveCharacter, User, UserRole, UserSession

AUTH_BASE = "https://login.eveonline.com/v2/oauth/authorize"
TOKEN_URL = "https://login.eveonline.com/v2/oauth/token"
VERIFY_URL = "https://login.eveonline.com/oauth/verify"
SESSION_COOKIE_NAME = "evearb_session"
SUPER_ADMIN_HANDLE = "Varaxian"
ROLE_USER = "user"
ROLE_ADMIN = "admin"
ROLE_SUPER_ADMIN = "super_admin"

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

def build_login_url(*, client_id: str, callback_url: str, scopes: str, state: str) -> str:
    params = {
        "response_type": "code",
        "redirect_uri": callback_url,
        "client_id": client_id,
        "scope": scopes,
        "state": state,
    }
    return f"{AUTH_BASE}?{urlencode(params)}"

async def exchange_code_for_token(*, code: str, client_id: str, client_secret: str, callback_url: str, user_agent: str) -> dict:
    basic = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("utf-8")
    headers = {
        "Authorization": f"Basic {basic}",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": user_agent,
    }
    data = {"grant_type": "authorization_code", "code": code, "redirect_uri": callback_url}
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(TOKEN_URL, headers=headers, data=data)
        response.raise_for_status()
        return response.json()

async def refresh_access_token(*, refresh_token: str, client_id: str, client_secret: str, user_agent: str) -> dict:
    basic = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("utf-8")
    headers = {
        "Authorization": f"Basic {basic}",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": user_agent,
    }
    data = {"grant_type": "refresh_token", "refresh_token": refresh_token}
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(TOKEN_URL, headers=headers, data=data)
        response.raise_for_status()
        return response.json()

async def verify_token(*, access_token: str, user_agent: str) -> dict:
    headers = {"Authorization": f"Bearer {access_token}", "User-Agent": user_agent}
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(VERIFY_URL, headers=headers)
        response.raise_for_status()
        return response.json()

def parse_expiry(token_data: dict) -> datetime | None:
    expires_in = token_data.get("expires_in")
    if expires_in is None:
        return None
    try:
        return utcnow() + timedelta(seconds=int(expires_in))
    except Exception:
        return None

def _is_varaxian_identity(*, handle: str | None = None, character_name: str | None = None) -> bool:
    return (handle or "").strip() == SUPER_ADMIN_HANDLE or (character_name or "").strip() == SUPER_ADMIN_HANDLE

def get_user_role(db: Session, user_id: int) -> str:
    row = db.query(UserRole).filter(UserRole.user_id == user_id).first()
    return row.role if row and row.role else ROLE_USER

def ensure_user_role(db: Session, user: User, *, character_name: str | None = None) -> UserRole:
    desired_role = ROLE_SUPER_ADMIN if _is_varaxian_identity(handle=user.handle, character_name=character_name) else ROLE_USER
    row = db.query(UserRole).filter(UserRole.user_id == user.id).first()
    if row is None:
        row = UserRole(user_id=user.id, role=desired_role)
        db.add(row)
        db.commit()
        db.refresh(row)
        return row
    if desired_role == ROLE_SUPER_ADMIN and row.role != ROLE_SUPER_ADMIN:
        row.role = ROLE_SUPER_ADMIN
        db.commit()
        db.refresh(row)
    return row

def set_user_role(db: Session, *, actor_user: User, target_user: User, role: str) -> UserRole:
    if role not in {ROLE_USER, ROLE_ADMIN, ROLE_SUPER_ADMIN}:
        raise HTTPException(status_code=400, detail="Invalid role")
    actor_role = get_user_role(db, actor_user.id)
    if actor_role != ROLE_SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Only super_admin can manage admins")
    if _is_varaxian_identity(handle=target_user.handle) and role != ROLE_SUPER_ADMIN:
        raise HTTPException(status_code=400, detail="Varaxian must remain super_admin")
    row = db.query(UserRole).filter(UserRole.user_id == target_user.id).first()
    if row is None:
        row = UserRole(user_id=target_user.id, role=role)
        db.add(row)
    else:
        row.role = role
    db.commit()
    db.refresh(row)
    return row

def upsert_user_from_esi(db: Session, *, token_data: dict, verify_data: dict) -> tuple[User, EveCharacter, EveAuthToken]:
    character_id = int(verify_data["CharacterID"])
    owner_hash = verify_data.get("CharacterOwnerHash")

    character = db.query(EveCharacter).filter(EveCharacter.character_id == character_id).first()
    user = None
    if character is not None:
        user = db.query(User).filter(User.id == character.user_id).first()

    if user is None and owner_hash:
        existing_character = db.query(EveCharacter).filter(EveCharacter.character_owner_hash == owner_hash).first()
        if existing_character is not None:
            user = db.query(User).filter(User.id == existing_character.user_id).first()

    if user is None:
        user = User(handle=verify_data.get("CharacterName"), is_active=True)
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.handle = verify_data.get("CharacterName", user.handle)
        user.is_active = True
        db.commit()
        db.refresh(user)

    if character is None:
        character = EveCharacter(
            user_id=user.id,
            character_id=character_id,
            character_name=verify_data.get("CharacterName", ""),
            client_id=verify_data.get("ClientID"),
            scopes=verify_data.get("Scopes"),
            character_owner_hash=owner_hash,
            token_type=token_data.get("token_type"),
            is_active=True,
        )
        db.add(character)
        db.commit()
        db.refresh(character)
    else:
        character.user_id = user.id
        character.character_name = verify_data.get("CharacterName", character.character_name)
        character.client_id = verify_data.get("ClientID")
        character.scopes = verify_data.get("Scopes")
        character.character_owner_hash = owner_hash
        character.token_type = token_data.get("token_type")
        character.is_active = True
        db.commit()
        db.refresh(character)

    ensure_user_role(db, user, character_name=character.character_name)

    token = (
        db.query(EveAuthToken)
        .filter(EveAuthToken.eve_character_id == character.id, EveAuthToken.is_active == True)
        .order_by(EveAuthToken.updated_at.desc())
        .first()
    )

    if token is None:
        token = EveAuthToken(
            user_id=user.id,
            eve_character_id=character.id,
            access_token=token_data.get("access_token", ""),
            refresh_token=token_data.get("refresh_token"),
            token_type=token_data.get("token_type"),
            scope_text=verify_data.get("Scopes"),
            expires_at=parse_expiry(token_data),
            is_active=True,
        )
        db.add(token)
    else:
        token.user_id = user.id
        token.access_token = token_data.get("access_token", token.access_token)
        token.refresh_token = token_data.get("refresh_token") or token.refresh_token
        token.token_type = token_data.get("token_type")
        token.scope_text = verify_data.get("Scopes")
        token.expires_at = parse_expiry(token_data)
        token.is_active = True

    db.commit()
    db.refresh(token)
    return user, character, token

def create_user_session(db: Session, user: User, *, days_valid: int = 30) -> UserSession:
    ensure_user_role(db, user)
    session = UserSession(
        user_id=user.id,
        session_token=secrets.token_urlsafe(48),
        is_active=True,
        expires_at=utcnow() + timedelta(days=days_valid),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def get_current_session_and_user(db: Session, session_token: str | None) -> tuple[UserSession | None, User | None]:
    if not session_token:
        return None, None

    session = (
        db.query(UserSession)
        .filter(UserSession.session_token == session_token, UserSession.is_active == True)
        .first()
    )
    if session is None:
        return None, None

    if session.expires_at is not None:
        expires_at = session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < utcnow():
            session.is_active = False
            db.commit()
            return None, None

    user = db.query(User).filter(User.id == session.user_id, User.is_active == True).first()
    if user is None:
        return None, None

    ensure_user_role(db, user)
    session.last_seen_at = utcnow()
    db.commit()
    return session, user

def get_current_user(
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> User:
    _, user = get_current_session_and_user(db, session_token)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

def get_current_user_optional(
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> User | None:
    _, user = get_current_session_and_user(db, session_token)
    return user

def get_current_session(
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> UserSession:
    session, user = get_current_session_and_user(db, session_token)
    if session is None or user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return session

def require_admin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    role = get_user_role(db, current_user.id)
    if role not in {ROLE_ADMIN, ROLE_SUPER_ADMIN}:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

def require_super_admin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    role = get_user_role(db, current_user.id)
    if role != ROLE_SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Super admin access required")
    return current_user

def latest_active_token_for_user(db: Session, user_id: int) -> EveAuthToken | None:
    return (
        db.query(EveAuthToken)
        .filter(EveAuthToken.user_id == user_id, EveAuthToken.is_active == True)
        .order_by(EveAuthToken.updated_at.desc())
        .first()
    )

def latest_characters_for_user(db: Session, user_id: int) -> list[EveCharacter]:
    return (
        db.query(EveCharacter)
        .filter(EveCharacter.user_id == user_id, EveCharacter.is_active == True)
        .order_by(EveCharacter.updated_at.desc())
        .all()
    )
