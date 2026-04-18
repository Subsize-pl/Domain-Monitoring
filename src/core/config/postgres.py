from typing import ClassVar
from urllib.parse import quote_plus
from pydantic import BaseModel, Field, SecretStr


class PostgresSettings(BaseModel):
    host: str
    port: int = Field(gt=0, lt=65536)
    user: str
    password: SecretStr
    db_name: str
    echo: bool

    naming_convention: ClassVar[dict[str, str]] = {
        "ix": "%(column_0_label)s_idx",
        "uq": "%(table_name)s_%(column_0_name)s_key",
        "ck": "%(table_name)s_%(constraint_name)s_check",
        "fk": "%(table_name)s_%(column_0_name)s_fkey",
        "pk": "%(table_name)s_pkey",
    }

    @property
    def asyncpg_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.user}:"
            f"{quote_plus(self.password.get_secret_value())}@"
            f"{self.host}:{self.port}/{self.db_name}"
        )
