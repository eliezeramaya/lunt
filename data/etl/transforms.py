"""
Data transformation utilities for ETL processes
"""


import pandas as pd


def validate_price_record(record: dict) -> bool:
    """Validate a single price record"""
    required_fields = ["insumo_code", "location_code", "price", "valid_from"]

    for field in required_fields:
        if field not in record or record[field] is None:
            return False

    if record["price"] <= 0:
        return False

    return True


def normalize_location_code(code: str) -> str:
    """Normalize location code format"""
    return code.strip().upper()


def normalize_insumo_code(code: str) -> str:
    """Normalize insumo code format"""
    return code.strip().upper()


def detect_outliers(df: pd.DataFrame, column: str, threshold: float = 3.0) -> pd.Series:
    """
    Detect outliers using z-score method
    Returns boolean Series indicating outliers
    """
    mean = df[column].mean()
    std = df[column].std()
    z_scores = (df[column] - mean) / std
    return abs(z_scores) > threshold


def aggregate_prices(df: pd.DataFrame, group_by: list[str]) -> pd.DataFrame:
    """
    Aggregate prices by specified columns
    Calculate mean, min, max prices
    """
    agg_dict = {
        "price": ["mean", "min", "max", "count"],
    }

    result = df.groupby(group_by).agg(agg_dict).reset_index()
    result.columns = ["_".join(col).strip("_") for col in result.columns.values]

    return result
