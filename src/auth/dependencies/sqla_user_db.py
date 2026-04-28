from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from auth.repositories.user import ExtendedSQLAlchemyUserDatabase
from infrastructure.db import db_manager
from auth.models.user import User


async def get_user_db(
    session: AsyncSession = Depends(db_manager.get_session),
) -> ExtendedSQLAlchemyUserDatabase:
    return ExtendedSQLAlchemyUserDatabase(session, User)
