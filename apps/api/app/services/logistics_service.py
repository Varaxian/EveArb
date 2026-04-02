from __future__ import annotations

from collections import deque

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.services.universe_service import get_graph, get_system_security, upsert_system_link

ESI_BASE_URL = "https://esi.evetech.net"

def classify_security(security: float) -> str:
    if security >= 0.5:
        return "highsec"
    if security > 0.0:
        return "lowsec"
    return "nullsec"

def classify_route_security(security_values: list[float]) -> dict:
    has_high = any(v >= 0.5 for v in security_values)
    has_low = any(0.0 < v < 0.5 for v in security_values)
    has_null = any(v <= 0.0 for v in security_values)

    if security_values and all(v >= 0.5 for v in security_values):
        profile = "highsec_only"
    elif has_null:
        profile = "includes_null"
    elif has_low:
        profile = "high_low"
    else:
        profile = "any"

    return {
        "has_highsec": has_high,
        "has_lowsec": has_low,
        "has_nullsec": has_null,
        "security_profile": profile,
        "min_security_on_path": min(security_values) if security_values else None,
        "max_security_on_path": max(security_values) if security_values else None,
    }

def route_passes_security_filters(
    *,
    security_values: list[float],
    route_security_mode: str,
    min_system_security: float,
) -> bool:
    if security_values:
        if min_system_security > 0 and min(security_values) < min_system_security:
            return False

    if route_security_mode == "any":
        return True
    if route_security_mode == "highsec_only":
        return all(v >= 0.5 for v in security_values)
    if route_security_mode == "no_null":
        return all(v > 0.0 for v in security_values)
    if route_security_mode == "lowsec_allowed":
        return all(v > 0.0 for v in security_values)
    if route_security_mode == "nullsec_allowed":
        return True
    return True

async def fetch_route_from_esi(origin_system_id: int, destination_system_id: int) -> list[int]:
    async with httpx.AsyncClient(base_url=ESI_BASE_URL, timeout=30.0, headers={"User-Agent": settings.esi_user_agent}) as client:
        response = await client.get(
            f"/v1/route/{origin_system_id}/{destination_system_id}/",
            params={"datasource": "tranquility"},
        )
        response.raise_for_status()
        return response.json()

def bfs_route(graph: dict[int, set[int]], origin_system_id: int, destination_system_id: int) -> list[int]:
    if origin_system_id == destination_system_id:
        return [origin_system_id]
    queue = deque([[origin_system_id]])
    seen = {origin_system_id}
    while queue:
        path = queue.popleft()
        node = path[-1]
        for neighbor in graph.get(node, set()):
            if neighbor in seen:
                continue
            new_path = path + [neighbor]
            if neighbor == destination_system_id:
                return new_path
            seen.add(neighbor)
            queue.append(new_path)
    return []

async def ensure_route_cached(db: Session, origin_system_id: int, destination_system_id: int) -> list[int]:
    path = await fetch_route_from_esi(origin_system_id, destination_system_id)
    if path and path[0] != origin_system_id:
        path = [origin_system_id] + path
    for i in range(len(path) - 1):
        upsert_system_link(db, path[i], path[i + 1])
        upsert_system_link(db, path[i + 1], path[i])
    db.commit()
    return path

async def analyze_route(db: Session, origin_system_id: int, destination_system_id: int) -> dict:
    graph = get_graph(db)
    path = bfs_route(graph, origin_system_id, destination_system_id)
    if not path:
        path = await ensure_route_cached(db, origin_system_id, destination_system_id)

    security_rows = []
    for system_id in path:
        security, name = await get_system_security(db, system_id, settings.esi_user_agent)
        security_rows.append({"system_id": system_id, "name": name, "security_status": security, "class": classify_security(security)})

    security_values = [row["security_status"] for row in security_rows]
    route_flags = classify_route_security(security_values)

    return {
        "route_system_ids": path,
        "route_jumps": max(len(path) - 1, 0),
        "systems": security_rows,
        **route_flags,
    }
