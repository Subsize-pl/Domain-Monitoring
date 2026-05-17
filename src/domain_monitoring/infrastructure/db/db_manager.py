from functools import cached_property, lru_cache
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from domain_monitoring.core.config.settings import get_settings

settings = get_settings()


class DbManager:
    def __init__(self):
        self._engine = create_async_engine(
            url=settings.postgres.asyncpg_url,
            echo=settings.debug,
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self._session_factory() as session:
            yield session

    @cached_property
    def async_session_factory(self) -> async_sessionmaker[AsyncSession]:
        return self._session_factory


@lru_cache(maxsize=1)
def get_db_manager() -> DbManager:
    return DbManager()
