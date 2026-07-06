"""
core/type_converter.py

Safe column-type conversion with validation and rollback.
"""

import pandas as pd
from typing import Dict, List

SUPPORTED_OVERRIDE_TYPES = [
    "string",
    "integer",
    "float",
    "boolean",
    "datetime",
    "category",
]


def convert_column(df: pd.DataFrame, col: str, target_type: str) -> pd.DataFrame:
    """
    Convert a single column to ``target_type``.

    Parameters
    ----------
    df : pd.DataFrame
    col : str
    target_type : str
        One of SUPPORTED_OVERRIDE_TYPES.

    Returns
    -------
    pd.DataFrame
        Copy with converted column.

    Raises
    ------
    ValueError
        If the conversion fails or type is unsupported.
    """
    if target_type not in SUPPORTED_OVERRIDE_TYPES:
        raise ValueError(
            f"Unsupported type '{target_type}'. Allowed: {SUPPORTED_OVERRIDE_TYPES}"
        )

    if col not in df.columns:
        raise ValueError(f"Column '{col}' not found in DataFrame.")

    df = df.copy()
    original = df[col].copy()

    try:
        if target_type == "string":
            df[col] = (
                df[col]
                .astype(str)
                .replace({"nan": pd.NA, "None": pd.NA, "": pd.NA})
            )
            df[col] = df[col].astype("string")

        elif target_type == "integer":
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].astype("Int64")

        elif target_type == "float":
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].astype("Float64")

        elif target_type == "boolean":
            bool_map = {
                "true": True,
                "True": True,
                "TRUE": True,
                "1": True,
                "yes": True,
                "Yes": True,
                "YES": True,
                "false": False,
                "False": False,
                "FALSE": False,
                "0": False,
                "no": False,
                "No": False,
                "NO": False,
            }
            df[col] = df[col].map(bool_map)
            df[col] = df[col].astype("boolean")

        elif target_type == "datetime":
            df[col] = pd.to_datetime(df[col], errors="coerce")

        elif target_type == "category":
            df[col] = df[col].astype("category")

    except Exception as e:
        df[col] = original
        raise ValueError(
            f"Failed to convert column '{col}' to {target_type}: {e}"
        )

    return df


def apply_type_overrides(df: pd.DataFrame, overrides: Dict[str, str]) -> tuple[pd.DataFrame, List[str]]:
    """
    Apply multiple type overrides.

    Returns
    -------
    tuple
        (updated DataFrame, list of error messages)
    """
    errors = []
    for col, target_type in overrides.items():
        try:
            df = convert_column(df, col, target_type)
        except ValueError as e:
            errors.append(str(e))
    return df, errors