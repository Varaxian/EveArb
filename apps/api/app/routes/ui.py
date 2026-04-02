
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse, RedirectResponse

from app.db.models import User
from app.services.auth_service import require_admin

router = APIRouter(tags=["ui"])

UI_DIR = Path(__file__).resolve().parents[1] / "ui"


def _read(name: str) -> str:
    return (UI_DIR / name).read_text(encoding="utf-8")


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return _read("dashboard.html")


@router.get("/active-opportunities", response_class=HTMLResponse)
def active_opportunities_page():
    return _read("dashboard.html")


@router.get("/administrator-settings", response_class=HTMLResponse)
def administrator_settings_page(current_user: User = Depends(require_admin)):
    return _read("administrator_settings.html")


@router.get("/admin")
def admin_redirect(current_user: User = Depends(require_admin)):
    return RedirectResponse(url="/administrator-settings", status_code=302)
