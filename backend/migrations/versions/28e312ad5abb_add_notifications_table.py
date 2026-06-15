"""add notifications table

Revision ID: 28e312ad5abb
Revises: fa26c8ce9a1b
Create Date: 2026-05-26 23:26:15.723862
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "28e312ad5abb"
down_revision: Union[str, None] = "fa26c8ce9a1b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.VARCHAR(length=36), autoincrement=False, nullable=False),
        sa.Column("org_id", sa.VARCHAR(length=36), autoincrement=False, nullable=False),
        sa.Column("user_id", sa.VARCHAR(length=36), autoincrement=False, nullable=True),
        sa.Column("type", sa.VARCHAR(length=50), autoincrement=False, nullable=False),
        sa.Column("title", sa.VARCHAR(length=255), autoincrement=False, nullable=False),
        sa.Column("message", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column("is_read", sa.BOOLEAN(), autoincrement=False, nullable=True),
        sa.Column("link", sa.VARCHAR(length=500), autoincrement=False, nullable=True),
        sa.Column("priority", sa.VARCHAR(length=20), autoincrement=False, nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], name=op.f("notifications_org_id_fkey")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("notifications_user_id_fkey")),
        sa.PrimaryKeyConstraint("id", name=op.f("notifications_pkey")),
    )


def downgrade() -> None:
    op.drop_table("notifications")
