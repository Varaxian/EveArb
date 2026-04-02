from __future__ import annotations

import csv
import io

def opportunities_to_csv(rows: list[dict]) -> str:
    if not rows:
        headers = [
            "type_id", "item_name", "src_region_id", "dst_region_id", "src_best_sell",
            "dst_best_buy", "taxes_unit", "hauling_cost_unit", "profit_per_unit",
            "roi", "max_qty_est", "route_jumps", "volume_m3", "total_m3",
            "net_profit_isk", "profit_per_m3"
        ]
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        return output.getvalue()

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()
