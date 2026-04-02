from __future__ import annotations

from typing import Iterable

import httpx

from app.services.auth_service import latest_active_token_for_user

ESI_BASE_URL = "https://esi.evetech.net"

_LOCATION_CACHE: dict[int, str | None] = {}

def _is_structure_id(location_id: int) -> bool:
    return int(location_id) >= 1000000000000

async def resolve_location_names(db, location_ids: Iterable[int], user_agent: str, user_id: int | None = None) -> dict[int, str | None]:
    ids = sorted({int(x) for x in location_ids if x})
    if not ids:
        return {}

    results: dict[int, str | None] = {}
    unresolved: list[int] = []

    for location_id in ids:
        if location_id in _LOCATION_CACHE:
            results[location_id] = _LOCATION_CACHE[location_id]
        else:
            unresolved.append(location_id)

    if unresolved:
        headers = {"User-Agent": user_agent}
        async with httpx.AsyncClient(base_url=ESI_BASE_URL, timeout=30.0, headers=headers) as client:
            # Try universe names first for everything. This resolves NPC stations cleanly.
            try:
                response = await client.post("/v3/universe/names/", params={"datasource": "tranquility"}, json=unresolved)
                if response.status_code < 400:
                    for row in response.json():
                        loc_id = int(row["id"])
                        name = row.get("name")
                        _LOCATION_CACHE[loc_id] = name
                        results[loc_id] = name
            except Exception:
                pass

            # Remaining unresolved IDs are treated as potential structures.
            remaining = [loc_id for loc_id in unresolved if loc_id not in results]
            access_token = None
            if user_id is not None:
                token_row = latest_active_token_for_user(db, user_id)
                if token_row and token_row.access_token:
                    access_token = token_row.access_token

            for loc_id in remaining:
                resolved_name = None
                if _is_structure_id(loc_id) and access_token:
                    try:
                        r = await client.get(
                            f"/v2/universe/structures/{loc_id}/",
                            params={"datasource": "tranquility"},
                            headers={"User-Agent": user_agent, "Authorization": f"Bearer {access_token}"},
                        )
                        if r.status_code < 400:
                            resolved_name = r.json().get("name")
                    except Exception:
                        resolved_name = None
                _LOCATION_CACHE[loc_id] = resolved_name
                results[loc_id] = resolved_name

    return {loc_id: results.get(loc_id) for loc_id in ids}
