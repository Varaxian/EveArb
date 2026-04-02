def recurrence_score(appearance_count: int, total_snapshots: int) -> float:
    if total_snapshots <= 0:
        return 0.0
    return appearance_count / total_snapshots
