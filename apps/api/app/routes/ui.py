from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["ui"])

def _read(name: str) -> str:
    html = Path(__file__).resolve().parents[1] / "ui" / name
    return html.read_text(encoding="utf-8")

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return _read("dashboard.html")

@router.get("/active-opportunities", response_class=HTMLResponse)
def active_opportunities_page():
    return _read("active_opportunities.html")

@router.get("/admin", response_class=HTMLResponse)
def admin_page():
    return _read("admin.html")
