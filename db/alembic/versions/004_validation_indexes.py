"""
Validation indexes for fast lookups

Adds/ensures composite indexes used by the validation service:

1) insumo_prices(insumo_id, location_code, valid_from DESC)
   - Optimiza seleccionar el precio vigente por insumo/ubicación/fecha

2) concept_recipes(concept_id)
   - Acelera carga de insumos por receta

Migration: 004
Depends on: 003_materialized_views
"""

from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create an additional DESC-ordered index to complement existing ones
    try:
        op.create_index(
            "ix_insumo_prices_insumo_loc_from_desc",
            "insumo_prices",
            ["insumo_id", "location_code", "valid_from"],
            unique=False,
            postgresql_ops={"valid_from": "DESC"},
        )
    except Exception:
        # If it already exists, ignore
        pass

    try:
        op.create_index(
            "ix_concept_recipes_concept",
            "concept_recipes",
            ["concept_id"],
            unique=False,
        )
    except Exception:
        pass


def downgrade() -> None:
    try:
        op.drop_index("ix_concept_recipes_concept", table_name="concept_recipes")
    except Exception:
        pass
    try:
        op.drop_index("ix_insumo_prices_insumo_loc_from_desc", table_name="insumo_prices")
    except Exception:
        pass

