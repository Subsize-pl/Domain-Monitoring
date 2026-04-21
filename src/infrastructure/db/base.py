import uuid

from sqlalchemy import MetaData, text
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION = {
    "ix": "%(column_0_label)s_idx",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_check",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}


class Base(DeclarativeBase):
    __abstract__ = True

    metadata = MetaData(
        naming_convention=NAMING_CONVENTION,
    )

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    _repr_cols_count = 3

    def __repr__(self) -> str:
        col_keys = self.__table__.columns.keys()[: self._repr_cols_count]
        cols = ", ".join([f"{c}: {getattr(self, c)}" for c in col_keys])
        return f"<{self.__class__.__name__} {cols}>"
