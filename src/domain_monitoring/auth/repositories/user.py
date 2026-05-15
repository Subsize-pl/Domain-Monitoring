from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy import select, func

from domain_monitoring.auth.models import User


class ExtendedSQLAlchemyUserDatabase(SQLAlchemyUserDatabase):
    async def get_by_username(self, username: str) -> User | None:
        query = select(self.user_table).where(
            func.lower(self.user_table.username) == username.lower(),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
