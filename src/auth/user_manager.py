import asyncio
import uuid

from fastapi import Request
from fastapi_users import BaseUserManager, UUIDIDMixin

from auth.config import AuthConfig
from auth.models.user import User
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
