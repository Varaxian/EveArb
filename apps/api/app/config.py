from __future__ import annotations

import json
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "EVE Arb"
    app_version: str = "v2.04"
    app_env: str = "production"
    public_base_url: str = "https://evearb-production.up.railway.app"

    database_url: str = "sqlite:///./eve_arb.db"

    esi_client_id: str = ""
    esi_client_secret: str = ""
    esi_callback_url: str = "https://evearb-production.up.railway.app/auth/callback"
    esi_scopes: str = "publicData"
    esi_user_agent: str = "EVEArb/2.04 (contact@example.com)"

    tracked_regions: str = "10000002,10000043"
    default_region_hub_systems: str = '{"10000002":30000142,"10000043":30002187,"10000032":30002659,"10000030":30002510,"10000042":30000144}'

    min_roi: float = 0.03
    min_qty: int = 10
    max_opportunity_rows: int = 250
    cost_per_m3_per_jump: float = 150.0
    base_trip_cost: float = 0.0
    sales_tax_rate: float = 0.075

    enable_scheduler: bool = False
    scheduler_interval_seconds: int = 900

    def tracked_region_ids(self) -> list[int]:
        return [int(x.strip()) for x in self.tracked_regions.split(",") if x.strip()]

    def region_hub_systems(self) -> dict[int, int]:
        raw = json.loads(self.default_region_hub_systems)
        return {int(k): int(v) for k, v in raw.items()}

settings = Settings()
