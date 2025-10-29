"""
Add materialized views for time series analysis

Creates:
1. concept_precios_mensuales (MV): Aggregated monthly price data per concept
   - Pre-computes monthly averages to avoid expensive aggregations at query time
   - Includes indirect costs and utility percentages
   - Refreshed by ETL after price updates

2. concept_pu_mensual (VIEW): Calculated unit prices with all factors
   - Builds on MV to add final calculations
   - Includes: base_price, indirect_cost, utility, final_price
   - Fast access for time series charting

Usage:
- /v1/series endpoint uses these views for fast chart generation
- ETL must call REFRESH MATERIALIZED VIEW CONCURRENTLY after updates
- CONCURRENTLY allows queries during refresh (requires UNIQUE index)

Performance impact:
- Without MV: O(n*m) where n=prices, m=recipes for each query
- With MV: O(k) where k=pre-computed monthly aggregates
- Typical speedup: 100x-1000x for historical series

NOTE: REFRESH MATERIALIZED VIEW CONCURRENTLY requires a UNIQUE index

Migration: 003
Depends on: 002_perf_indexes
"""

from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create materialized view and dependent view for concept pricing series."""

    # Create materialized view for monthly aggregated concept prices
    # NOTE: This MV must be refreshed after price updates (see ETL)
    op.execute(
        """
        CREATE MATERIALIZED VIEW concept_precios_mensuales AS
        SELECT
            c.id AS concept_id,
            c.code AS concept_code,
            c.name AS concept_name,
            l.id AS location_id,
            l.code AS location_code,
            DATE_TRUNC('month', ip.valid_from) AS month,
            AVG(ip.price * cr.quantity) AS base_price_avg,
            STDDEV(ip.price * cr.quantity) AS base_price_stddev,
            COUNT(DISTINCT ip.id) AS price_samples,
            AVG(c.indirect_percentage) AS indirect_percentage,
            AVG(c.utility_percentage) AS utility_percentage
        FROM concepts c
        INNER JOIN concept_recipes cr ON c.id = cr.concept_id
        INNER JOIN insumos i ON cr.insumo_id = i.id
        INNER JOIN insumo_prices ip ON i.id = ip.insumo_id
        INNER JOIN locations l ON cr.location_id = l.id AND ip.location_id = l.id
        WHERE ip.valid_from >= NOW() - INTERVAL '24 months'  -- Last 2 years only
        GROUP BY
            c.id, c.code, c.name,
            l.id, l.code,
            DATE_TRUNC('month', ip.valid_from),
            c.indirect_percentage, c.utility_percentage
        ORDER BY month DESC, concept_code, location_code
    """
    )

    # Create UNIQUE index for CONCURRENTLY refresh support
    # NOTE: This allows queries during refresh without blocking
    op.execute(
        """
        CREATE UNIQUE INDEX ix_concept_precios_mensuales_unique
        ON concept_precios_mensuales (concept_id, location_id, month)
    """
    )

    # Create regular view for final calculated prices
    # NOTE: This is a simple view, not materialized, built on top of the MV
    op.execute(
        """
        CREATE VIEW concept_pu_mensual AS
        SELECT
            concept_id,
            concept_code,
            concept_name,
            location_id,
            location_code,
            month,
            base_price_avg,
            base_price_stddev,
            price_samples,
            indirect_percentage,
            utility_percentage,
            base_price_avg * (1 + indirect_percentage) AS price_with_indirect,
            base_price_avg * (1 + indirect_percentage) * (1 + utility_percentage) AS final_unit_price
        FROM concept_precios_mensuales
        ORDER BY month DESC, concept_code, location_code
    """
    )


def downgrade() -> None:
    """Drop views."""
    op.execute("DROP VIEW IF EXISTS concept_pu_mensual")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS concept_precios_mensuales")
