from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DM Transaction Service"
    debug: bool = False
    log_level: str = "INFO"
    database_url: str = "sqlite:///./data/database.db"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"

    # Configurações de retry
    retry_ttl_ms: int = 5000  # 5 segundos
    max_retries: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
