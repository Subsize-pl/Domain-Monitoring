import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, DateTime, Enum, Index, desc, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infrastructure.db.base import Base
from monitoring.models.domain_status import MonitorStatus

if TYPE_CHECKING:
    from monitoring.models import Domain


class DomainCheck(Base):
    __tablename__ = "domain_check"
    __table_args__ = (
        Index(
            None,
            "domain_id",
            desc("checked_at"),
        ),
    )

    domain_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("domain.id", ondelete="CASCADE"),
    )

    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    status: Mapped[MonitorStatus] = mapped_column(
        Enum(MonitorStatus, name="monitor_status"),
    )

    http_status_code: Mapped[int | None]
    latency_ms: Mapped[int | None]
    error_text: Mapped[str | None]

    domain: Mapped["Domain"] = relationship(back_populates="checks")
