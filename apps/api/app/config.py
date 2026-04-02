from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "EVE Arb"
    app_version: str = "v2.02"
    app_env: str = "production"
    public_base_url: str = "https://evearb-production.up.railway.app"

    esi_client_id: str = ""
    esi_client_secret: str = ""
    esi_callback_url: str = "https://evearb-production.up.railway.app/auth/callback"
    esi_scopes: str = "publicData"
    esi_user_agent: str = "EVEArb/2.02 (contact@example.com)"

settings = Settings()
