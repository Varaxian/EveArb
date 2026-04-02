from __future__ import annotations

from collections import defaultdict
from typing import AsyncIterator, Iterable

import httpx

ESI_BASE_URL = "https://esi.evetech.net"

async def stream_region_orders(region_id: int, user_agent: str) -> AsyncIterator[list[dict]]:
    headers = {"User-Agent": user_agent}
    params = {"datasource": "tranquility", "order_type": "all", "page": 1}

    async with httpx.AsyncClient(base_url=ESI_BASE_URL, timeout=60.0, headers=headers) as client:
        first = await client.get(f"/v1/markets/{region_id}/orders/", params=params)
        first.raise_for_status()
        first_page = first.json()
        yield first_page
        pages = int(first.headers.get("X-Pages", "1"))

        for page in range(2, pages + 1):
            response = await client.get(
                f"/v1/markets/{region_id}/orders/",
                params={"datasource": "tranquility", "order_type": "all", "page": page},
            )
            response.raise_for_status()
            yield response.json()

def new_aggregate_row() -> dict:
    return {
        "best_sell": None,
        "best_buy": None,
        "sell_volume": 0,
        "buy_volume": 0,
        "best_sell_location_id": None,
        "best_buy_location_id": None,
    }

def update_aggregates(agg: dict[int, dict], orders_page: Iterable[dict]) -> dict[int, dict]:
    for order in orders_page:
        type_id = int(order["type_id"])
        price = float(order["price"])
        volume = int(order.get("volume_remain", 0) or 0)
        location_id = int(order.get("location_id", 0) or 0)
        is_buy = bool(order["is_buy_order"])

        row = agg.setdefault(type_id, new_aggregate_row())

        if is_buy:
            if row["best_buy"] is None or price > row["best_buy"]:
                row["best_buy"] = price
                row["buy_volume"] = volume
                row["best_buy_location_id"] = location_id
            elif price == row["best_buy"]:
                row["buy_volume"] += volume
        else:
            if row["best_sell"] is None or price < row["best_sell"]:
                row["best_sell"] = price
                row["sell_volume"] = volume
                row["best_sell_location_id"] = location_id
            elif price == row["best_sell"]:
                row["sell_volume"] += volume

    return agg

def aggregate_best_prices(orders: Iterable[dict]) -> dict[int, dict]:
    agg: dict[int, dict] = defaultdict(new_aggregate_row)
    return update_aggregates(agg, orders)
