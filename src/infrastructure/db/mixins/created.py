from datetime import datetime
from auth.utils import utc_now
from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class CreatedMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=utc_now,
        nullable=False,
    )
