"""
Prefect ETL Flow for Price Updates
Extracts, transforms and loads price data from external sources
"""

import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from prefect import flow, task

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
    Load price data to database
    Uses append-only strategy for immutable history
    """
    # TODO: Implement actual database load with SQLAlchemy
    # For now, save to temporary file
    output_path = "/tmp/lunt_prices_loaded.csv"
    df.to_csv(output_path, index=False)
    print(f"Loaded {len(df)} records to {output_path}")
    return len(df)


@flow(name="Price Update ETL")
def price_update_flow(source_path: str) -> int:
    """
    Main ETL flow for updating prices
    """
    print("Starting Price Update ETL Flow")

    # Extract
    raw_data = extract_price_data(source_path)

    # Transform
    clean_data = transform_price_data(raw_data)

    # Load
    connection_string = os.getenv("DATABASE_URL", "postgresql://lunt_user:lunt_pass@localhost:5432/lunt_db")
    records_loaded = load_price_data(clean_data, connection_string)

    print(f"ETL Flow completed. {records_loaded} records loaded.")
    return records_loaded


if __name__ == "__main__":
    # Example usage
    import argparse

    parser = argparse.ArgumentParser(description="Run Price Update ETL")
    parser.add_argument("--source", default="data/seed/insumo_precios.csv", help="Source CSV file")
    args = parser.parse_args()

    price_update_flow(args.source)
