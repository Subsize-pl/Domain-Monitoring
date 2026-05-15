from urllib.parse import quote_plus
from pydantic import BaseModel, Field, SecretStr


class PostgresSettings(BaseModel):
    scheme: str = "postgresql+asyncpg"

    host: str
    port: int
    user: str
    password: SecretStr
    db_name: str

    @property
    def asyncpg_url(self) -> str:
        print(
            (
                f"{self.scheme}://{self.user}:"
                f"{quote_plus(self.password.get_secret_value())}@"
                f"{self.host}:{self.port}/{self.db_name}"
            )
        )
        return (
            f"{self.scheme}://{self.user}:"
            f"{quote_plus(self.password.get_secret_value())}@"
            f"{self.host}:{self.port}/{self.db_name}"
        )
