"""
Create preview_log table for analytics and re-training dataset

Revision: 006
Depends on: 005
"""

from alembic import op
import sqlalchemy as sa


revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "preview_log",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("correlation_id", sa.String(length=36), nullable=True),
        sa.Column("user_id", sa.String(length=128), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=8), nullable=True),
        sa.Column("inferred_concept_code", sa.String(length=100), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("alternatives", sa.JSON(), nullable=True),
        sa.Column("final_concept_code", sa.String(length=100), nullable=True),
        sa.Column("was_correct", sa.Boolean(), nullable=True),
        sa.Column("selection_mode", sa.String(length=20), nullable=True),
        sa.Column("recipe_variant_id", sa.String(length=50), nullable=True),
        sa.Column("strategy", sa.String(length=50), nullable=True),
        sa.Column("ubicacion_codigo", sa.String(length=20), nullable=True),
        sa.Column("fecha", sa.Date(), nullable=True),
        sa.Column("porcentajes", sa.JSON(), nullable=True),
        sa.Column("preview_summary", sa.JSON(), nullable=True),
        sa.Column("source_backend", sa.String(length=20), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_preview_log_created", "preview_log", ["created_at"], unique=False)
    op.create_index("ix_preview_log_inferred", "preview_log", ["inferred_concept_code"], unique=False)
    op.create_index("ix_preview_log_final", "preview_log", ["final_concept_code"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_preview_log_final", table_name="preview_log")
    op.drop_index("ix_preview_log_inferred", table_name="preview_log")
    op.drop_index("ix_preview_log_created", table_name="preview_log")
    op.drop_table("preview_log")

