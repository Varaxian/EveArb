from dataclasses import dataclass

@dataclass
class LoadCandidate:
    type_id: int
    item_name: str
    buy_price_unit: float
    sell_price_unit: float
    quantity: int
    volume_per_unit_m3: float
