from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.orm import Session

from app.db.models import UniverseSystem, UniverseSystemLink

ESI_BASE_URL = "https://esi.evetech.net"

def _is_fresh(updated_at: datetime | None, hours: int = 24) -> bool:
    if updated_at is None:
        return False
    now = datetime.now(timezone.utc)
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)
    return updated_at >= now - timedelta(hours=hours)

async def fetch_system_details(system_id: int, user_agent: str) -> dict:
    headers = {"User-Agent": user_agent}
    async with httpx.AsyncClient(base_url=ESI_BASE_URL, timeout=30.0, headers=headers) as client:
        response = await client.get(f"/v4/universe/systems/{system_id}/", params={"datasource": "tranquility"})
        response.raise_for_status()
        return response.json()

async def get_system_security(db: Session, system_id: int, user_agent: str) -> tuple[float, str | None]:
    row = db.query(UniverseSystem).filter(UniverseSystem.system_id == system_id).first()
    if row and _is_fresh(row.updated_at):
        return float(row.security_status or 0.0), row.name

    data = await fetch_system_details(system_id, user_agent)
    if row is None:
        row = UniverseSystem(system_id=system_id)
        db.add(row)
    row.name = data.get("name")
    row.security_status = float(data.get("security_status") or 0.0)
    db.commit()
    db.refresh(row)
    return float(row.security_status or 0.0), row.name

def upsert_system_link(db: Session, from_system_id: int, to_system_id: int) -> None:
    exists = (
        db.query(UniverseSystemLink)
        .filter(
            UniverseSystemLink.from_system_id == from_system_id,
            UniverseSystemLink.to_system_id == to_system_id,
        )
        .first()
    )
    if exists is None:
        db.add(UniverseSystemLink(from_system_id=from_system_id, to_system_id=to_system_id))

def get_graph(db: Session) -> dict[int, set[int]]:
    graph: dict[int, set[int]] = defaultdict(set)
    rows = db.query(UniverseSystemLink).all()
    for row in rows:
        graph[row.from_system_id].add(row.to_system_id)
    return graph
