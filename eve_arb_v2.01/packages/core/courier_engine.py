def recommend_courier_mode(total_profit: float, courier_reward: float) -> str:
    return "COURIER" if total_profit > courier_reward else "SELF"
