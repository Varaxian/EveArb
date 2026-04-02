from packages.core.models import LoadCandidate

def total_m3(load: LoadCandidate) -> float:
    return load.volume_per_unit_m3 * load.quantity

def total_profit(load: LoadCandidate) -> float:
    return (load.sell_price_unit - load.buy_price_unit) * load.quantity
