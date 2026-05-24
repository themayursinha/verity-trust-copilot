"""Add performance indexes

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-24
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_evidence_org_id", "evidence_records", ["org_id"])
    op.create_index("ix_answers_generation_id", "answers", ["generation_id"])
    op.create_index("ix_answer_generations_org_id", "answer_generations", ["org_id"])
    op.create_index("ix_approvals_answer_id", "approvals", ["answer_id"])
    op.create_index("ix_approvals_user_id", "approvals", ["user_id"])
    op.create_index("ix_policies_org_id", "policies", ["org_id"])
    op.create_index("ix_pentests_org_id", "pentests", ["org_id"])
    op.create_index("ix_audit_logs_org_id", "audit_logs", ["org_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_evidence_org_id")
    op.drop_index("ix_answers_generation_id")
    op.drop_index("ix_answer_generations_org_id")
    op.drop_index("ix_approvals_answer_id")
    op.drop_index("ix_approvals_user_id")
    op.drop_index("ix_policies_org_id")
    op.drop_index("ix_pentests_org_id")
    op.drop_index("ix_audit_logs_org_id")
    op.drop_index("ix_audit_logs_created_at")
