from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from core.utils.config import get_settings


class DbManager:
    def __init__(self):
        settings = get_settings()
        self.engine = create_async_engine(
            url=settings.postgres.asyncpg_url,
            echo=settings.postgres.echo,
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.session_factory() as session:
            yield session


db_manager = DbManager()
