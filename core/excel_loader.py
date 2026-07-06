"""
core/excel_loader.py

Excel file loading utilities with sheet detection, password-protection
detection, and per-sheet loading.
"""

import pandas as pd
from dataclasses import dataclass
from typing import List, Optional

from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ExcelInfo:
    """Metadata about an Excel workbook."""
    sheet_names: List[str]
    selected_sheet: Optional[str]
    password_protected: bool = False
    error: Optional[str] = None


def get_excel_info(file_input) -> ExcelInfo:
    """
    Inspect an Excel workbook for sheet names and password protection.

    Parameters
    ----------
    file_input : file-like
        Streamlit UploadedFile or any file-like object.

    Returns
    -------
    ExcelInfo
    """
    try:
        try:
            file_input.seek(0)
        except Exception:
            pass

        xl = pd.ExcelFile(file_input)
        sheets = xl.sheet_names

        return ExcelInfo(
            sheet_names=sheets,
            selected_sheet=sheets[0] if sheets else None,
            password_protected=False,
        )

    except Exception as e:
        error_msg = str(e)
        logger.exception("Excel inspection failed")

        if any(k in error_msg.lower() for k in ("password", "encrypted", "decrypt")):
            return ExcelInfo(
                sheet_names=[],
                selected_sheet=None,
                password_protected=True,
                error="Password-protected Excel file detected.",
            )

        return ExcelInfo(
            sheet_names=[],
            selected_sheet=None,
            password_protected=False,
            error=f"Could not read Excel file: {error_msg}",
        )


def load_excel_sheet(file_input, sheet_name: str, header_row: int = 0) -> pd.DataFrame:
    """
    Load a specific sheet from an Excel workbook.

    Parameters
    ----------
    file_input : file-like
    sheet_name : str
        Name or index of the sheet.
    header_row : int
        0-based row index to use as the header.

    Returns
    -------
    pd.DataFrame

    Raises
    ------
    ValueError
        If the sheet cannot be loaded.
    """
    try:
        try:
            file_input.seek(0)
        except Exception:
            pass

        df = pd.read_excel(file_input, sheet_name=sheet_name, header=header_row)
        return df

    except Exception as e:
        logger.exception("Excel sheet loading failed")
        raise ValueError(f"Failed to load sheet '{sheet_name}': {e}")