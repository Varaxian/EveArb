from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.logistics_service import analyze_route

router = APIRouter(prefix="/logistics", tags=["logistics"])

@router.get("/route")
async def logistics_route(
    from_system: int = Query(...),
    to_system: int = Query(...),
    db: Session = Depends(get_db),
):
    return await analyze_route(db, from_system, to_system)
