from pydantic_settings import BaseSettings, SettingsConfigDict

class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    worker_poll_interval_seconds: int = 900
    worker_mode: str = "run_once"

settings = WorkerSettings()
