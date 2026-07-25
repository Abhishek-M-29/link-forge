from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://abhishek:user1234@127.0.0.1:5432/link_forge"
    base_url: str = "http://localhost:8000"
    jwt_secret_key: str = "supersecretkey_please_change_in_production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
DATABASE_URL = settings.database_url

