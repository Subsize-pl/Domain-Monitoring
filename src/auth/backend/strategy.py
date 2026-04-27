from fastapi_users.authentication import Strategy

from auth.models.user import User
from auth.services import AuthSessionService
from auth.user_manager import UserManager


class SessionStrategy(Strategy):
    def __init__(self, service: AuthSessionService) -> None:
        self.service = service

    async def write_token(self, user: User) -> str:
        return await self.service.create_session(user.id)

    async def read_token(
        self,
        token: str | None,
        user_manager: UserManager,
    ) -> User | None:
        if not token:
            return None

        user_id = await self.service.get_user_id_by_session_id(token)
        if user_id is None:
            return None

        return await user_manager.get(user_id)

    async def destroy_token(self, token: str, user: User) -> None:
        await self.service.revoke_session(token)
