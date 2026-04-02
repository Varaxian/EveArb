from __future__ import annotations

import json
from typing import Any


def safe_json_loads(value: str | None) -> Any:
    if not value:
        return None
    try:
        return json.loads(value)
    except Exception:
        return {"raw": value}
