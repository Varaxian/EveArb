from __future__ import annotations

import httpx

ESI_BASE_URL = "https://esi.evetech.net"

async def resolve_region_names(region_ids: list[int], user_agent: str) -> dict[int, str]:
    ids = sorted({int(x) for x in region_ids if x})
    if not ids:
        return {}

    headers = {"User-Agent": user_agent}
    async with httpx.AsyncClient(base_url=ESI_BASE_URL, timeout=30.0, headers=headers) as client:
        response = await client.post("/v3/universe/names/", params={"datasource": "tranquility"}, json=ids)
        response.raise_for_status()
        payload = response.json()

    names: dict[int, str] = {}
    for row in payload:
        try:
            names[int(row.get("id"))] = row.get("name") or str(row.get("id"))
        except Exception:
            continue
    return names
