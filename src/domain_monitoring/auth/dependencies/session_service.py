from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from domain_monitoring.auth.config import AuthConfig
from domain_monitoring.core.config.settings import get_settings
from domain_monitoring.infrastructure.db.db_manager import get_db_manager

from domain_monitoring.auth.cache.session import AuthSessionCache
from domain_monitoring.auth.repositories.session import AuthSessionRepository
from domain_monitoring.auth.services.session import AuthSessionService

db_manager = get_db_manager()


def get_auth_session_service(
    session: AsyncSession = Depends(db_manager.get_session),
) -> AuthSessionService:
    settings = get_settings()
    return AuthSessionService(
        cache=AuthSessionCache(settings.redis.redis_url),
        repo=AuthSessionRepository(session),
        session_ttl=AuthConfig.session_ttl,
    )
