import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AuthRedisKeys:
    session_user_prefix: str = "auth:session:user:"
    user_sessions_prefix: str = "auth:user:sessions:"

    def session_user(self, session_id: uuid.UUID) -> str:
        return f"{self.session_user_prefix}{str(session_id)}"

    def user_sessions(self, user_id: uuid.UUID) -> str:
        return f"{self.user_sessions_prefix}{str(user_id)}"
