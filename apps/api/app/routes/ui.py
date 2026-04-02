from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["ui"])

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    html = Path(__file__).resolve().parents[1] / "ui" / "dashboard.html"
    return html.read_text(encoding="utf-8")
