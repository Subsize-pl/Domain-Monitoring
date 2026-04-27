from fastapi import Depends

from auth.dependencies.sqla_user_db import get_user_db
from auth.user_manager import UserManager
from core.config import get_settings
from infrastructure.mailing.service import get_mail_service

settings = get_settings()
mail_service = get_mail_service()


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(
        user_db=user_db,
        mail_service=mail_service,
        app_base_url=settings.app_base_url,
    )
