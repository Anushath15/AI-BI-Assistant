"""
core/header_detector.py

Automatic header-row detection for tabular files that contain
metadata rows above the actual column headers.
"""

import pandas as pd
from typing import Optional

from utils.logger import get_logger

logger = get_logger(__name__)


def detect_header_row(df_raw: pd.DataFrame, max_rows: int = 10) -> int:
    """
    Inspect the first ``max_rows`` rows and return the index of the
    row that is most likely the header.

    Scoring strategy
    ----------------
    * Count non-empty, non-null values.
    * Bonus for string-like values (headers are usually text, not numbers).
    * The row with the highest score wins.
    """
    if df_raw.empty:
        return 0

    inspect_count = min(max_rows, len(df_raw))
    best_row = 0
    best_score = -1.0

    for i in range(inspect_count):
        row = df_raw.iloc[i]
        non_empty = 0
        string_like = 0
        total = 0

        for val in row:
            total += 1
            if pd.isna(val):
                continue
            s = str(val).strip()
            if not s:
                continue

            non_empty += 1

            # Prefer text values over pure numbers
            try:
                float(s)
            except ValueError:
                string_like += 1

        if total == 0:
            continue

        string_ratio = string_like / total if total > 0 else 0
        score = non_empty + (string_ratio * non_empty * 0.5)

        if score > best_score:
            best_score = score
            best_row = i

    logger.info("Detected header row: %d (score=%.2f)", best_row, best_score)
    return best_row


def apply_header(df_raw: pd.DataFrame, header_row: int) -> pd.DataFrame:
    """
    Promote ``header_row`` to column names and drop all rows above it.

    Parameters
    ----------
    df_raw : pd.DataFrame
        DataFrame loaded without a header (all rows treated as data).
    header_row : int
        0-based index of the header row.

    Returns
    -------
    pd.DataFrame
    """
    if header_row >= len(df_raw):
        header_row = 0

    df = df_raw.iloc[header_row:].reset_index(drop=True)
    header_values = df.iloc[0]

    df.columns = [
        str(v).strip() if pd.notna(v) else f"Column_{i}"
        for i, v in enumerate(header_values)
    ]

    # Remove the header row from the data
    df = df.iloc[1:].reset_index(drop=True)

    # Deduplicate column names
    df = _deduplicate_columns(df)

    return df


def _deduplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Append numeric suffixes to duplicate column names."""
    cols = list(df.columns)
    seen = {}
    new_cols = []

    for c in cols:
        if c in seen:
            seen[c] += 1
            new_cols.append(f"{c}_{seen[c]}")
        else:
            seen[c] = 0
            new_cols.append(c)

    df.columns = new_cols
    return df