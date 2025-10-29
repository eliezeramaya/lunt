"""
Add performance indexes for fast queries

Creates composite indexes to optimize frequent query patterns:

1. insumo_prices: (insumo_id, location_id, valid_from DESC)
   - Optimizes: "Get latest price for insumo X in location Y"
   - Used by: Preview and recalc endpoints when fetching current prices
   - Impact: O(log n) instead of O(n) for price lookups

2. concept_recipes: (concept_id, location_id)
   - Optimizes: "Get all ingredients for concept X in location Y"
   - Used by: All calculation endpoints when expanding recipes
   - Impact: Faster recipe lookups for regional variations

3. drafts: (user_id, created_at DESC)
   - Optimizes: "Get recent drafts for user X"
   - Used by: User dashboard and draft listing
   - Impact: Faster pagination and recent item queries

NOTE: These indexes use DESC ordering for valid_from/created_at to optimize
"get latest" queries which are the most common access pattern.

Migration: 002
Depends on: 001_initial_schema
"""

import sqlalchemy as sa
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create performance indexes."""

    # Index for fast price lookups by insumo and location, ordered by date DESC
    # NOTE: DESC ordering allows efficient "get latest price" queries
    op.create_index(
        "ix_insumo_prices_lookup",
        "insumo_prices",
        ["insumo_id", "location_id", "valid_from"],
        unique=False,
        postgresql_ops={"valid_from": "DESC"},
    )

    # Index for fast recipe lookups by concept and location
    # NOTE: Covers the most common query pattern in calculations
    op.create_index(
        "ix_concept_recipes_lookup",
        "concept_recipes",
        ["concept_id", "location_id"],
        unique=False,
    )

    # Index for user draft queries ordered by creation date
    # NOTE: DESC ordering for "recent first" pagination
    op.create_index(
        "ix_drafts_user_created",
        "drafts",
        ["user_id", "created_at"],
        unique=False,
        postgresql_ops={"created_at": "DESC"},
    )

    # Index for quote lookups by user and status
    # NOTE: Optimizes filtering confirmed quotes by user
    op.create_index(
        "ix_quotes_user_status",
        "quotes",
        ["user_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    """Remove performance indexes."""
    op.drop_index("ix_quotes_user_status", table_name="quotes")
    op.drop_index("ix_drafts_user_created", table_name="drafts")
    op.drop_index("ix_concept_recipes_lookup", table_name="concept_recipes")
    op.drop_index("ix_insumo_prices_lookup", table_name="insumo_prices")
