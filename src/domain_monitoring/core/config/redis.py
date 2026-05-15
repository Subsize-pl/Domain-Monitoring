from pydantic import BaseModel, Field


class RedisSettings(BaseModel):
    host: str
    port: int

    @property
    def redis_url(self) -> str:
        print(f"redis://{self.host}:{self.port}/0")
        return f"redis://{self.host}:{self.port}/0"
