from __future__ import annotations

import base64
from urllib.parse import urlencode

import httpx

AUTH_BASE = "https://login.eveonline.com/v2/oauth/authorize"
TOKEN_URL = "https://login.eveonline.com/v2/oauth/token"
VERIFY_URL = "https://login.eveonline.com/oauth/verify"

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

async def verify_token(*, access_token: str, user_agent: str) -> dict:
    headers = {"Authorization": f"Bearer {access_token}", "User-Agent": user_agent}
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(VERIFY_URL, headers=headers)
        response.raise_for_status()
        return response.json()
