from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_name: str = "eve_arb_v2.01"
    database_url: str = "postgresql+psycopg://eve:eve@localhost:5432/evearb"
    redis_url: str = "redis://localhost:6379/0"
    eve_sso_client_id: str = ""
    eve_sso_client_secret: str = ""
    eve_sso_redirect_uri: str = "http://localhost:8000/api/v1/auth/eve/callback"
    session_secret: str = "replace-me"

settings = Settings()
