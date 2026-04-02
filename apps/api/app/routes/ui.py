from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse, RedirectResponse

from app.db.models import User
from app.services.auth_service import require_admin

router = APIRouter(tags=["ui"])

def _dashboard_html() -> str:
    html = Path(__file__).resolve().parents[1] / "ui" / "dashboard.html"
    return html.read_text(encoding="utf-8")

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return _dashboard_html()

@router.get("/active-opportunities", response_class=HTMLResponse)
def active_opportunities():
    return _dashboard_html()

@router.get("/administrator-settings", response_class=HTMLResponse)
def administrator_settings(current_user: User = Depends(require_admin)):
    return _dashboard_html()

@router.get("/admin", include_in_schema=False)
def admin_redirect(current_user: User = Depends(require_admin)):
    return RedirectResponse(url="/administrator-settings", status_code=307)
