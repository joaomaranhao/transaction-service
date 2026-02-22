from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DM Transaction Service"
    debug: bool = False
    log_level: str = "INFO"
    database_url: str = "sqlite:///./transactions.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
