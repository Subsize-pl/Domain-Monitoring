from fastapi import Depends
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db import db_manager
from auth.models.user import User


async def get_user_db(
    session: AsyncSession = Depends(db_manager.get_session),
) -> SQLAlchemyUserDatabase:
    return SQLAlchemyUserDatabase(session, User)
