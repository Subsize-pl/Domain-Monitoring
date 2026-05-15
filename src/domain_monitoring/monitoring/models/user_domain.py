import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from domain_monitoring.infrastructure.db.base import Base
from domain_monitoring.infrastructure.db.mixins import CreatedMixin
from domain_monitoring.monitoring.config import MonitoringConfig

if TYPE_CHECKING:
    from domain_monitoring.auth.models import User
    from domain_monitoring.monitoring.models.domain import Domain


class UserDomain(Base, CreatedMixin):
    __tablename__ = "user_domain"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "domain_id",
            name="user_domain_user_id_domain_id_key",
        ),
        Index(None, "user_id"),
        Index(None, "domain_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
    )

    domain_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("domain.id", ondelete="CASCADE"),
    )

    title: Mapped[str | None] = mapped_column(
        String(MonitoringConfig.MAX_DOMAIN_TITLE_LENGTH),
    )

    user: Mapped["User"] = relationship(
        back_populates="user_domains",
        lazy="noload",
    )
    domain: Mapped["Domain"] = relationship(
        back_populates="user_domains",
        lazy="noload",
    )
