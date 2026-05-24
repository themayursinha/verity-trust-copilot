"""Add branding columns to organizations

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("organizations", sa.Column("brand_color", sa.String(7), server_default="#0f766e"))
    op.add_column("organizations", sa.Column("logo_url", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("organizations", "logo_url")
    op.drop_column("organizations", "brand_color")
