from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gps_collection_enabled: bool = True
    gps_collection_interval_seconds: int = 10
    gps_stale_after_seconds: int = 45
    gps_source_url: str = "https://www.montevideo.gub.uy/buses/rest/stm-online"


settings = Settings()
