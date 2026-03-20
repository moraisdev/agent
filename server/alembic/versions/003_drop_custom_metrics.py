"""Drop unused custom_metrics column from user_preferences."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None

_SCHEMA = "agent_memory"


def upgrade() -> None:
    op.drop_column("user_preferences", "custom_metrics", schema=_SCHEMA)


def downgrade() -> None:
    op.add_column(
        "user_preferences",
        sa.Column("custom_metrics", JSONB, server_default="{}", nullable=False),
        schema=_SCHEMA,
    )
