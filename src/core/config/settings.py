from functools import cached_property
from pathlib import Path

from anyio.functools import lru_cache
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from .postgres import PostgresSettings
from .redis import RedisSettings

BASE_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    postgres_host: str
    postgres_port: int
    postgres_user: str
    postgres_password: SecretStr
    postgres_db: str
    postgres_echo: bool = False

    redis_host: str
    redis_port: int
    redis_session_ttl: int = 3600

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        extra="ignore",
        case_sensitive=False,
    )

    @cached_property
    def postgres(self) -> PostgresSettings:
        return PostgresSettings(
            host=self.postgres_host,
            port=self.postgres_port,
            user=self.postgres_user,
            password=self.postgres_password,
            db_name=self.postgres_db,
            echo=self.postgres_echo,
        )

    @cached_property
    def redis(self) -> RedisSettings:
        return RedisSettings(
            host=self.redis_host,
            port=self.redis_port,
            session_ttl=self.redis_session_ttl,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
