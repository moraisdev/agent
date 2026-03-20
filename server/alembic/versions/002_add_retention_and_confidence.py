"""Add sample_count to learned_patterns, confidence check, user_id format check."""

import sqlalchemy as sa
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None

_SCHEMA = "agent_memory"


def upgrade() -> None:
    op.add_column(
        "learned_patterns",
        sa.Column("sample_count", sa.Integer, server_default="0", nullable=False),
        schema=_SCHEMA,
    )

    op.create_check_constraint(
        "ck_confidence_range",
        "learned_patterns",
        "confidence >= 0.0 AND confidence <= 1.0",
        schema=_SCHEMA,
    )

    op.create_check_constraint(
        "ck_user_id_format",
        "user_preferences",
        "user_id ~ '^[0-9]{10,15}$' OR user_id ~ '^[a-zA-Z0-9._-]+$'",
        schema=_SCHEMA,
    )


def downgrade() -> None:
    op.drop_constraint("ck_user_id_format", "user_preferences", schema=_SCHEMA)
    op.drop_constraint("ck_confidence_range", "learned_patterns", schema=_SCHEMA)
    op.drop_column("learned_patterns", "sample_count", schema=_SCHEMA)
