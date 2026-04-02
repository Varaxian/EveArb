
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse, RedirectResponse

from app.services.auth_service import require_admin

router = APIRouter(tags=["ui"])


def _html(name: str) -> str:
    html = Path(__file__).resolve().parents[1] / "ui" / name
    return html.read_text(encoding="utf-8")


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return _html("dashboard.html")


@router.get("/active-opportunities", response_class=HTMLResponse)
def active_opportunities():
    return _html("active_opportunities.html")


@router.get("/administrator-settings", response_class=HTMLResponse)
def administrator_settings(current_user = Depends(require_admin)):
    return _html("administrator_settings.html")


@router.get("/admin")
def admin_redirect(current_user = Depends(require_admin)):
    return RedirectResponse(url="/administrator-settings", status_code=302)
