from dataclasses import dataclass
from pydantic import BaseModel, Field


@dataclass(frozen=True, slots=True)
class AuthRedisKeys:
    session_user_prefix: str = "auth:session:user:"
    user_sessions_prefix: str = "auth:user:sessions:"

    def session_user(self, session_id: str) -> str:
        return f"{self.session_user_prefix}{session_id}"

    def user_sessions(self, user_id: str) -> str:
        return f"{self.user_sessions_prefix}{user_id}"


class RedisSettings(BaseModel):
    host: str
    port: int = Field(gt=0, lt=65536)
    session_ttl: int = Field(default=3600, ge=1)

    @property
    def redis_url(self) -> str:
        return f"redis://{self.host}:{self.port}/0"


auth_redis_keys = AuthRedisKeys()
