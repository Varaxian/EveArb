from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable

import httpx
from sqlalchemy.orm import Session

from app.db.models import LocationNameCache
from app.services.auth_service import latest_active_token_for_user

ESI_BASE_URL = "https://esi.evetech.net"
NPC_KINDS = {"station", "solar_system", "constellation", "region"}
STRUCTURE_REFRESH_HOURS = 12
UNRESOLVED_RETRY_HOURS = 6

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

def _is_structure_id(location_id: int) -> bool:
    return int(location_id) >= 1000000000000

def _is_fresh(row: LocationNameCache | None) -> bool:
    if row is None or row.last_checked_at is None:
        return False
    checked = row.last_checked_at
    if checked.tzinfo is None:
        checked = checked.replace(tzinfo=timezone.utc)
    age = utcnow() - checked
    if row.location_kind in NPC_KINDS and row.is_resolved:
        return True
    if row.is_resolved:
        return age <= timedelta(hours=STRUCTURE_REFRESH_HOURS)
    return age <= timedelta(hours=UNRESOLVED_RETRY_HOURS)

def _upsert_cache_row(db: Session, location_id: int, name: str | None, kind: str | None, is_resolved: bool) -> None:
    row = db.query(LocationNameCache).filter(LocationNameCache.location_id == location_id).first()
    now = utcnow()
    if row is None:
        row = LocationNameCache(
            location_id=location_id,
            location_name=name,
            location_kind=kind,
            is_resolved=is_resolved,
            first_seen_at=now,
            last_checked_at=now,
        )
        db.add(row)
    else:
        row.location_name = name
        row.location_kind = kind
        row.is_resolved = is_resolved
        row.last_checked_at = now

async def warm_location_cache(db: Session, location_ids: Iterable[int], user_agent: str) -> None:
    ids = sorted({int(x) for x in location_ids if x})
    if not ids:
        return

    rows = {
        row.location_id: row
        for row in db.query(LocationNameCache).filter(LocationNameCache.location_id.in_(ids)).all()
    }
    missing = [loc_id for loc_id in ids if not _is_structure_id(loc_id) and not _is_fresh(rows.get(loc_id))]
    if not missing:
        return

    headers = {"User-Agent": user_agent}
    async with httpx.AsyncClient(base_url=ESI_BASE_URL, timeout=30.0, headers=headers) as client:
        try:
            response = await client.post("/v3/universe/names/", params={"datasource": "tranquility"}, json=missing)
            if response.status_code < 400:
                returned = set()
                for row in response.json():
                    loc_id = int(row["id"])
                    returned.add(loc_id)
                    _upsert_cache_row(
                        db,
                        location_id=loc_id,
                        name=row.get("name"),
                        kind=row.get("category"),
                        is_resolved=bool(row.get("name")),
                    )
                for loc_id in missing:
                    if loc_id not in returned:
                        _upsert_cache_row(db, location_id=loc_id, name=None, kind="station", is_resolved=False)
        except Exception:
            for loc_id in missing:
                if loc_id not in rows:
                    _upsert_cache_row(db, location_id=loc_id, name=None, kind="station", is_resolved=False)
    db.commit()

async def resolve_location_names(db: Session, location_ids: Iterable[int], user_agent: str, user_id: int | None = None) -> dict[int, str | None]:
    ids = sorted({int(x) for x in location_ids if x})
    if not ids:
        return {}

    rows = {
        row.location_id: row
        for row in db.query(LocationNameCache).filter(LocationNameCache.location_id.in_(ids)).all()
    }

    results: dict[int, str | None] = {}
    unresolved_station_ids: list[int] = []
    unresolved_structure_ids: list[int] = []

    for loc_id in ids:
        row = rows.get(loc_id)
        if _is_fresh(row):
            results[loc_id] = row.location_name if row.is_resolved else None
            continue
        if _is_structure_id(loc_id):
            unresolved_structure_ids.append(loc_id)
        else:
            unresolved_station_ids.append(loc_id)

    headers = {"User-Agent": user_agent}
    async with httpx.AsyncClient(base_url=ESI_BASE_URL, timeout=30.0, headers=headers) as client:
        if unresolved_station_ids:
            try:
                response = await client.post("/v3/universe/names/", params={"datasource": "tranquility"}, json=unresolved_station_ids)
                returned = set()
                if response.status_code < 400:
                    for row in response.json():
                        loc_id = int(row["id"])
                        returned.add(loc_id)
                        name = row.get("name")
                        kind = row.get("category")
                        _upsert_cache_row(db, loc_id, name, kind, bool(name))
                        results[loc_id] = name
                for loc_id in unresolved_station_ids:
                    if loc_id not in returned:
                        _upsert_cache_row(db, loc_id, None, "station", False)
                        results[loc_id] = None
            except Exception:
                for loc_id in unresolved_station_ids:
                    _upsert_cache_row(db, loc_id, None, "station", False)
                    results[loc_id] = None

        access_token = None
        if unresolved_structure_ids and user_id is not None:
            token_row = latest_active_token_for_user(db, user_id)
            if token_row and token_row.access_token:
                access_token = token_row.access_token

        for loc_id in unresolved_structure_ids:
            resolved_name = None
            if access_token:
                try:
                    response = await client.get(
                        f"/v2/universe/structures/{loc_id}/",
                        params={"datasource": "tranquility"},
                        headers={"User-Agent": user_agent, "Authorization": f"Bearer {access_token}"},
                    )
                    if response.status_code < 400:
                        resolved_name = response.json().get("name")
                except Exception:
                    resolved_name = None
            _upsert_cache_row(db, loc_id, resolved_name, "structure", bool(resolved_name))
            results[loc_id] = resolved_name

    db.commit()

    for loc_id in ids:
        if loc_id not in results:
            row = rows.get(loc_id)
            results[loc_id] = row.location_name if row and row.is_resolved else None

    return results
