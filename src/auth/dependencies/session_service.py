from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from auth.config import AuthConfig
from core.config import get_settings
from infrastructure.db import db_manager

from auth.cache.session import AuthSessionCache
from auth.repositories.session import AuthSessionRepository
from auth.services.session import AuthSessionService


def get_auth_session_service(
    session: AsyncSession = Depends(db_manager.get_session),
) -> AuthSessionService:
    settings = get_settings()
    return AuthSessionService(
        cache=AuthSessionCache(settings.redis.redis_url),
        repo=AuthSessionRepository(session),
        session_ttl=AuthConfig.session_ttl,
    )
