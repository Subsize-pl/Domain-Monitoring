from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy import select, func

from auth.models import User


class ExtendedSQLAlchemyUserDatabase(SQLAlchemyUserDatabase):
    async def get_by_username(self, username: str) -> User | None:
        statement = select(self.user_table).where(
            func.lower(self.user_table.username) == username.lower(),
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()
