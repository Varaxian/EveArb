from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse

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
def administrator_settings_page():
    return _dashboard_html()

@router.get("/admin")
def admin_redirect():
    return RedirectResponse(url="/administrator-settings", status_code=307)
