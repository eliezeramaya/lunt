"""
p1.2 – Soporte para múltiples recetas por concepto

Agrega columnas en concept_recipes para soportar variantes:
- variant_id (STRING, NOT NULL)
- variant_label (STRING, NULL)
- recipe_code (STRING, NULL)
- active (BOOLEAN, NOT NULL, default TRUE)

e índices:
- (concept_id, variant_id)
- (concept_id, active)

Migration: 005
Depends on: 004_validation_indexes
"""

import sqlalchemy as sa
from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("concept_recipes", sa.Column("variant_id", sa.String(length=50), nullable=False, server_default="default"))
    op.add_column("concept_recipes", sa.Column("variant_label", sa.String(length=100), nullable=True))
    op.add_column("concept_recipes", sa.Column("recipe_code", sa.String(length=50), nullable=True))
    op.add_column("concept_recipes", sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")))

    # Create indexes
    op.create_index("ix_concept_recipes_concept_variant", "concept_recipes", ["concept_id", "variant_id"], unique=False)
    op.create_index("ix_concept_recipes_active", "concept_recipes", ["concept_id", "active"], unique=False)

    # Drop server defaults after data backfill (optional)
    op.alter_column("concept_recipes", "variant_id", server_default=None)
    op.alter_column("concept_recipes", "active", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_concept_recipes_active", table_name="concept_recipes")
    op.drop_index("ix_concept_recipes_concept_variant", table_name="concept_recipes")
    op.drop_column("concept_recipes", "active")
    op.drop_column("concept_recipes", "recipe_code")
    op.drop_column("concept_recipes", "variant_label")
    op.drop_column("concept_recipes", "variant_id")

