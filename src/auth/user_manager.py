import asyncio
import uuid

from fastapi import Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users import BaseUserManager, UUIDIDMixin

from auth.config import AuthConfig
from auth.models.user import User
from auth.schemas import UserCreate
from infrastructure.mailing.service import MailService


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    verification_token_secret = "SuperSecretToken"

    def __init__(
        self,
        user_db,
        mail_service: MailService,
        app_base_url: str,
    ):
        super().__init__(user_db)
        self.mail_service = mail_service
        self.app_base_url = app_base_url.rstrip("/")

    async def on_after_request_verify(
        self,
        user: User,
        token: str,
        request: Request | None = None,
    ) -> None:
        verification_link = (
            f"{self.app_base_url}{AuthConfig.api_prefix}/verify?token={token}"
        )

        asyncio.create_task(
            self.mail_service.send_verification_email(
                user.email,
                username=user.username,
                verification_link=verification_link,
            ),
        )

    async def authenticate(
        self,
        credentials: OAuth2PasswordRequestForm,
    ) -> User | None:
        username = credentials.username.strip()

        if not username or not credentials.password:
            return None

        user = await self.user_db.get_by_username(username)

        if user is None:
            return None

        if not user.is_active:
            return None

        verified, updated_password = self.password_helper.verify_and_update(
            credentials.password,
            user.hashed_password,
        )

        if not verified:
            return None

        if updated_password is not None:
            await self.user_db.update(
                user,
                {"hashed_password": updated_password},
            )

        return user

    async def get_by_email(self, user_email: str) -> User | None:
        return await self.user_db.get_by_email(user_email)

    async def create(
        self,
        user_create: UserCreate,
        safe: bool = False,
        request: Request | None = None,
    ) -> User | None:
        await self.validate_password(user_create.password, user_create)

        existing_user = await self.user_db.get_by_email(user_create.email)
        if existing_user is not None:
            return None

        user_dict = (
            user_create.create_update_dict()
            if safe
            else user_create.create_update_dict_superuser()
        )
        password = user_dict.pop("password")
        user_dict["hashed_password"] = self.password_helper.hash(password)

        created_user = await self.user_db.create(user_dict)

        await self.on_after_register(created_user, request)

        return created_user
