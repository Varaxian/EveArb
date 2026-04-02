from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.orm import Session

from app.db.models import TypeMetadata

ESI_BASE_URL = "https://esi.evetech.net"

def _is_fresh(updated_at: datetime | None, hours: int = 24) -> bool:
    if updated_at is None:
        return False
    now = datetime.now(timezone.utc)
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)
    return updated_at >= now - timedelta(hours=hours)

async def get_route_jumps(origin_system_id: int, destination_system_id: int, user_agent: str) -> int:
    if origin_system_id == destination_system_id:
        return 0
    headers = {"User-Agent": user_agent}
    async with httpx.AsyncClient(base_url=ESI_BASE_URL, timeout=30.0, headers=headers) as client:
        response = await client.get(
            f"/v1/route/{origin_system_id}/{destination_system_id}/",
            params={"datasource": "tranquility"},
        )
        response.raise_for_status()
        route = response.json()
    return max(len(route) - 1, 0)

async def get_type_volume_m3(db: Session, type_id: int, user_agent: str) -> tuple[float, str | None]:
    cached = db.query(TypeMetadata).filter(TypeMetadata.type_id == type_id).first()
    if cached and _is_fresh(cached.updated_at):
        return float(cached.volume_m3 or 0.0), cached.name

    headers = {"User-Agent": user_agent}
    async with httpx.AsyncClient(base_url=ESI_BASE_URL, timeout=30.0, headers=headers) as client:
        response = await client.get(f"/v3/universe/types/{type_id}/", params={"datasource": "tranquility"})
        response.raise_for_status()
        data = response.json()

    if cached is None:
        cached = TypeMetadata(type_id=type_id)
        db.add(cached)

    cached.name = data.get("name")
    packaged_volume = data.get("packaged_volume")
    volume = packaged_volume if packaged_volume is not None else data.get("volume")
    cached.volume_m3 = float(volume or 0.0)
    db.commit()
    db.refresh(cached)

    return float(cached.volume_m3 or 0.0), cached.name
