from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from domain_monitoring.auth.repositories.user import ExtendedSQLAlchemyUserDatabase
from domain_monitoring.infrastructure.db.db_manager import get_db_manager
from domain_monitoring.auth.models.user import User

db_manager = get_db_manager()


async def get_user_db(
    session: AsyncSession = Depends(db_manager.get_session),
) -> ExtendedSQLAlchemyUserDatabase:
    return ExtendedSQLAlchemyUserDatabase(session, User)
