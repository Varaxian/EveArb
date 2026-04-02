from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import RegionMarketSnapshot
from app.services.esi_market import stream_region_orders, update_aggregates
from app.services.location_name_service import warm_location_cache

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

async def ingest_regions(db: Session, region_ids: list[int]) -> dict:
    snapshot_at = utcnow()
    inserted_rows = 0
    summary = []
    npc_location_ids: list[int] = []

    for region_id in region_ids:
        agg: dict[int, dict] = {}
        orders_fetched = 0
        pages_fetched = 0

        async for orders_page in stream_region_orders(region_id=region_id, user_agent=settings.esi_user_agent):
            pages_fetched += 1
            orders_fetched += len(orders_page)
            update_aggregates(agg, orders_page)

        for type_id, row in agg.items():
            best_sell_location_id = row.get("best_sell_location_id")
            best_buy_location_id = row.get("best_buy_location_id")
            if best_sell_location_id and int(best_sell_location_id) < 1000000000000:
                npc_location_ids.append(int(best_sell_location_id))
            if best_buy_location_id and int(best_buy_location_id) < 1000000000000:
                npc_location_ids.append(int(best_buy_location_id))

            db.add(
                RegionMarketSnapshot(
                    snapshot_at=snapshot_at,
                    region_id=region_id,
                    type_id=type_id,
                    best_sell=row["best_sell"],
                    best_buy=row["best_buy"],
                    sell_volume=row["sell_volume"],
                    buy_volume=row["buy_volume"],
                    best_sell_location_id=best_sell_location_id,
                    best_buy_location_id=best_buy_location_id,
                )
            )
            inserted_rows += 1

        summary.append({
            "region_id": region_id,
            "pages_fetched": pages_fetched,
            "orders_fetched": orders_fetched,
            "types_aggregated": len(agg),
        })

    db.commit()

    # Resolve static NPC names after commit, but keep this out of the request path in v2.13+.
    # Leaving the helper imported for future non-blocking warm paths.
    _ = warm_location_cache
    _ = npc_location_ids

    return {
        "status": "ok",
        "snapshot_at": snapshot_at.isoformat(),
        "regions": summary,
        "rows_inserted": inserted_rows,
    }
