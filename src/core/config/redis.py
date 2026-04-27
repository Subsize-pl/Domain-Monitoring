from pydantic import BaseModel, Field


class RedisSettings(BaseModel):
    host: str
    port: int = Field(gt=0, lt=65536)

    @property
    def redis_url(self) -> str:
        return f"redis://{self.host}:{self.port}/0"
