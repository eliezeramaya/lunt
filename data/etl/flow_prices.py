"""
Prefect ETL Flow for Price Updates
Extracts, transforms and loads price data from external sources

NOTE: After loading prices, this flow refreshes the materialized view
concept_precios_mensuales for fast time series queries.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from prefect import flow, task
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).parent.parent))


@task
def extract_price_data(source_path: str) -> pd.DataFrame:
    """
    Extract price data from CSV source
    TODO: Add support for multiple data sources (APIs, databases, etc.)
    """
    df = pd.read_csv(source_path)
    print(f"Extracted {len(df)} records from {source_path}")
    return df


@task
def transform_price_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform and validate price data
    - Clean data
    - Validate formats
    - Add metadata
    """
    df = df.copy()

    # Validate required columns
    required_columns = ["insumo_code", "location_code", "price", "currency", "valid_from"]
    missing = set(required_columns) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Clean data
    df["insumo_code"] = df["insumo_code"].str.strip().str.upper()
    df["location_code"] = df["location_code"].str.strip().str.upper()
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["valid_from"] = pd.to_datetime(df["valid_from"])

    # Remove nulls
    df = df.dropna()

    # Add source metadata
    df["source"] = "ETL_MANUAL"
    df["loaded_at"] = datetime.now()

    print(f"Transformed {len(df)} valid records")
    return df


@task
def load_price_data(df: pd.DataFrame, connection_string: str) -> int:
    """
    Load price data to database.
    Uses append-only strategy for immutable history.
    """
    # TODO: Implement actual database load with SQLAlchemy
    # For now, save to temporary file
    output_path = "/tmp/lunt_prices_loaded.csv"
    df.to_csv(output_path, index=False)
    print(f"Loaded {len(df)} records to {output_path}")
    return len(df)


@task
def refresh_materialized_view(connection_string: str) -> None:
    """
    Refresh materialized view for time series analysis.

    Uses CONCURRENTLY to avoid blocking queries during refresh.
    This requires a UNIQUE index on the MV (created in migration 003).

    NOTE: If this fails with "relation does not exist", run migrations:
    alembic upgrade head

    Performance:
    - CONCURRENTLY: Queries can run during refresh, but refresh takes longer
    - Without CONCURRENTLY: Faster refresh, but table is locked
    """
    try:
        engine = create_engine(connection_string)
        with engine.connect() as conn:
            # Refresh materialized view concurrently (non-blocking)
            # NOTE: This works because we have a UNIQUE index from migration 003
            conn.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY concept_precios_mensuales"))
            conn.commit()
            print("✓ Materialized view refreshed successfully (CONCURRENTLY)")
    except Exception as e:
        # If MV doesn't exist yet (migrations not run), log warning but don't fail
        # TODO: Consider making this mandatory once migrations are deployed
        print(f"⚠ Warning: Could not refresh materialized view: {e}")
        print("  Hint: Run 'alembic upgrade head' to create materialized views")
    finally:
        engine.dispose()


@flow(name="Price Update ETL")
def price_update_flow(source_path: str) -> int:
    """
    Main ETL flow for updating prices.

    Steps:
    1. Extract data from source
    2. Transform and validate
    3. Load to database
    4. Refresh materialized view for fast queries

    NOTE: Step 4 is critical for maintaining query performance on /v1/series endpoint
    """
    print("Starting Price Update ETL Flow")

    # Extract
    raw_data = extract_price_data(source_path)

    # Transform
    clean_data = transform_price_data(raw_data)

    # Load
    connection_string = os.getenv(
        "DATABASE_URL", "postgresql://lunt_user:lunt_pass@localhost:5432/lunt_db"
    )
    records_loaded = load_price_data(clean_data, connection_string)

    # Refresh materialized view (non-blocking)
    # NOTE: This ensures time series queries remain fast
    refresh_materialized_view(connection_string)

    print(f"ETL Flow completed. {records_loaded} records loaded.")
    return records_loaded


if __name__ == "__main__":
    # Example usage
    import argparse

    parser = argparse.ArgumentParser(description="Run Price Update ETL")
    parser.add_argument("--source", default="data/seed/insumo_precios.csv", help="Source CSV file")
    args = parser.parse_args()

    price_update_flow(args.source)
