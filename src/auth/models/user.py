from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.db.base import Base
from infrastructure.db.mixins import CreatedMixin, UpdatedMixin


class User(Base, SQLAlchemyBaseUserTableUUID, CreatedMixin, UpdatedMixin):
    username: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        unique=True,
        index=True,
    )
