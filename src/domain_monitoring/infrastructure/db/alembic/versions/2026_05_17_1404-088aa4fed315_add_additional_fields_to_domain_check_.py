"""Add additional fields to domain check model

Revision ID: 088aa4fed315
Revises: ba9772aae1d2
Create Date: 2026-05-17 14:04:28.902306
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "088aa4fed315"
down_revision: Union[str, Sequence[str], None] = "ba9772aae1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE domain_protocol AS ENUM ('https', 'http')",
    )
    op.execute(
        "CREATE TYPE tls_status AS ENUM ('valid', 'invalid', 'not_checked')",
    )

    op.add_column(
        "domain_check",
        sa.Column(
            "attempt_count",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )
    op.add_column(
        "domain_check",
        sa.Column(
            "scheme_used",
            sa.Enum(
                "https",
                "http",
                name="domain_protocol",
                create_type=False,
            ),
            nullable=True,
        ),
    )
    op.add_column(
        "domain_check",
        sa.Column(
            "tls_status",
            sa.Enum(
                "valid",
                "invalid",
                "not_checked",
                name="tls_status",
                create_type=False,
            ),
            nullable=False,
            server_default="not_checked",
        ),
    )


def downgrade() -> None:
    op.drop_column("domain_check", "tls_status")
    op.drop_column("domain_check", "scheme_used")
    op.drop_column("domain_check", "attempt_count")

    op.execute("DROP TYPE IF EXISTS domain_protocol")
    op.execute("DROP TYPE IF EXISTS tls_status")
