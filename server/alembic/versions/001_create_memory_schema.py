import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "001"
down_revision = None
branch_labels = None
depends_on = None

_SCHEMA = "agent_memory"


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {_SCHEMA}")

    op.create_table(
        "user_preferences",
        sa.Column("user_id", sa.String(100), primary_key=True),
        sa.Column("preferred_time_range", sa.String(20), server_default="this_month"),
        sa.Column("preferred_report_type", sa.String(20), server_default="business"),
        sa.Column("preferred_language", sa.String(10), server_default="pt-BR"),
        sa.Column("preferred_format", sa.String(10), server_default="text"),
        sa.Column("custom_metrics", JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema=_SCHEMA,
    )

    op.create_table(
        "report_history",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(100), nullable=False),
        sa.Column("report_type", sa.String(20), nullable=False),
        sa.Column("time_range", sa.String(20), nullable=False),
        sa.Column("key_metrics", JSONB, server_default="{}"),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_report_history_user_date",
        "report_history",
        ["user_id", "generated_at"],
        schema=_SCHEMA,
    )

    op.create_table(
        "learned_patterns",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("pattern_type", sa.String(50), nullable=False),
        sa.Column("pattern_key", sa.String(100), nullable=False),
        sa.Column("pattern_value", JSONB, nullable=False),
        sa.Column("confidence", sa.Float, server_default="0.5"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema=_SCHEMA,
    )
    op.create_unique_constraint(
        "uq_pattern_type_key",
        "learned_patterns",
        ["pattern_type", "pattern_key"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_pattern_type_key",
        "learned_patterns",
        ["pattern_type", "pattern_key"],
        schema=_SCHEMA,
    )


def downgrade() -> None:
    op.drop_table("learned_patterns", schema=_SCHEMA)
    op.drop_table("report_history", schema=_SCHEMA)
    op.drop_table("user_preferences", schema=_SCHEMA)
    op.execute(f"DROP SCHEMA IF EXISTS {_SCHEMA}")
