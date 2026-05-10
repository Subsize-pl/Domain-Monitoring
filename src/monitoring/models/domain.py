from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infrastructure.db.base import Base
from infrastructure.db.mixins import CreatedMixin

if TYPE_CHECKING:
    from .domain_check import DomainCheck
    from .user_domain import UserDomain


class Domain(Base, CreatedMixin):
    __tablename__ = "domain"

    name: Mapped[str] = mapped_column(
        String(253),
        unique=True,
    )

    is_enabled: Mapped[bool] = mapped_column(default=True)
    is_archived: Mapped[bool] = mapped_column(default=False)

    checks: Mapped[list["DomainCheck"]] = relationship(
        back_populates="domain",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="DomainCheck.checked_at.desc()",
    )

    user_domains: Mapped[list["UserDomain"]] = relationship(
        back_populates="domain",
        cascade="all, delete-orphan",
    )
