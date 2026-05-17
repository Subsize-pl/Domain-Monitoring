from fastapi import Depends

from domain_monitoring.auth.dependencies.sqla_user_db import get_user_db
from domain_monitoring.auth.user_manager import UserManager
from domain_monitoring.core.config.settings import get_settings
from domain_monitoring.infrastructure.mailing.service import get_mail_service

settings = get_settings()
mail_service = get_mail_service()


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(
        user_db=user_db,
        mail_service=mail_service,
        app_base_url=settings.urls.APP_BASE,
    )
