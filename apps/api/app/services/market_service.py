from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import RegionMarketSnapshot
from app.services.esi_market import aggregate_best_prices, fetch_region_orders

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

async def ingest_regions(db: Session, region_ids: list[int]) -> dict:
    snapshot_at = utcnow()
    inserted_rows = 0
    summary = []
    npc_location_ids: list[int] = []

    for region_id in region_ids:
        orders = await fetch_region_orders(region_id=region_id, user_agent=settings.esi_user_agent)
        agg = aggregate_best_prices(orders)

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
            "orders_fetched": len(orders),
            "types_aggregated": len(agg),
        })

    db.commit()


    return {
        "status": "ok",
        "snapshot_at": snapshot_at.isoformat(),
        "regions": summary,
        "rows_inserted": inserted_rows,
    }
