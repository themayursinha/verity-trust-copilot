"""add webhooks and webhook_logs tables

Revision ID: e75550fd0708
Revises: 28e312ad5abb
Create Date: 2026-05-26 23:30:13.262785
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'e75550fd0708'
down_revision: Union[str, None] = '28e312ad5abb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('webhooks',
    sa.Column('id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('org_id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('url', sa.VARCHAR(length=500), autoincrement=False, nullable=False),
    sa.Column('secret', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('name', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('events', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('is_active', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('custom_headers', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('webhooks_pkey'))
    )
    op.create_table('webhook_logs',
    sa.Column('id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('webhook_id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('org_id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('event', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('payload', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('response_status', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('response_body', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('success', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('error', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('webhook_logs_pkey'))
    )


def downgrade() -> None:
    op.drop_table('webhook_logs')
    op.drop_table('webhooks')