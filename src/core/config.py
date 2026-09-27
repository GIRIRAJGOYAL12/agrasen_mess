from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL



class Settings(BaseSettings):
    app_name: str = "Hostel Mess Management API"
    debug: bool = False
    app_timezone: str = "Asia/Kolkata"
    qr_expiry_seconds: int = 60

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str
    db_user: str
    db_password: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

