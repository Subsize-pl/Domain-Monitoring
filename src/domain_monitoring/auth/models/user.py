from typing import TYPE_CHECKING

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from domain_monitoring.infrastructure.db.base import Base
from domain_monitoring.infrastructure.db.mixins import CreatedMixin, UpdatedMixin

if TYPE_CHECKING:
    from domain_monitoring.monitoring.models.user_domain import UserDomain


MAX_USERNAME_LENGTH = 128


class User(Base, SQLAlchemyBaseUserTableUUID, CreatedMixin, UpdatedMixin):
    __tablename__ = "user"

    username: Mapped[str] = mapped_column(
        String(MAX_USERNAME_LENGTH),
        unique=True,
        index=True,
    )

    user_domains: Mapped[list["UserDomain"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="noload",
    )
