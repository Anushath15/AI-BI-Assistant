import io
import logging
from dataclasses import dataclass
from typing import Optional, Union

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------

# Maximum file size accepted (50 MB). Adjust for your deployment.
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024

# Encodings tried in order. utf-8-sig handles the BOM that Excel adds.
ENCODING_FALLBACK_ORDER = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]

# Maximum rows loaded. Protects against accidentally uploading a
# multi-million-row warehouse export.
MAX_ROWS = 500_000

# Supported file extensions
SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class LoadResult:
    """
    Represents the outcome of a load attempt.

    Implements __iter__ so callers can unpack it as a tuple:
        success, result = load_csv(file)

    This preserves backward compatibility with app.py while giving
    us a proper typed object internally.
    """

    success: bool
    data: Optional[pd.DataFrame] = None
    error: Optional[str] = None
    encoding_used: Optional[str] = None
    file_size_bytes: Optional[int] = None
    rows_loaded: Optional[int] = None
    file_type: Optional[str] = None
    file_name: Optional[str] = None

    def __iter__(self):
        """
        Allow tuple unpacking: success, result = load_result
        When success is True,  result is the DataFrame.
        When success is False, result is the error string.
        """
        if self.success:
            yield self.success
            yield self.data
        else:
            yield self.success
            yield self.error

    def __repr__(self) -> str:
        if self.success:
            return (
                f"LoadResult(success=True, rows={self.rows_loaded}, "
                f"encoding='{self.encoding_used}')"
            )
        return f"LoadResult(success=False, error='{self.error}')"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _read_bytes(file_input) -> bytes:
    """
    Read raw bytes from either a Streamlit UploadedFile or a file path.

    Streamlit's UploadedFile is a file-like object. After reading it,
    the internal pointer moves to the end, so we reset it with seek(0)
    in case the caller tries to read it again later.
    """
    if isinstance(file_input, (str, bytes)):
        # Plain file path string
        with open(file_input, "rb") as f:
            return f.read()

    # File-like object (Streamlit UploadedFile, BytesIO, etc.)
    content = file_input.read()
    try:
        file_input.seek(0)
    except Exception:
        pass  # Some file-like objects don't support seek; ignore.
    return content


def _decode_csv(raw_bytes: bytes) -> tuple[str, str]:
    """
    Try each encoding in ENCODING_FALLBACK_ORDER until one succeeds.

    Returns (decoded_string, encoding_used).
    Raises ValueError if all encodings fail.
    """
    for encoding in ENCODING_FALLBACK_ORDER:
        try:
            return raw_bytes.decode(encoding), encoding
        except (UnicodeDecodeError, LookupError):
            continue

    raise ValueError(
        "Could not decode the file. "
        f"Tried encodings: {', '.join(ENCODING_FALLBACK_ORDER)}. "
        "Please re-save the CSV as UTF-8."
    )


def _detect_file_type(file_name: str) -> str:
    """
    Detect file type from filename extension.
    Returns: 'csv', 'xlsx', 'xls', or raises ValueError.
    """
    if not file_name:
        raise ValueError("Cannot determine file type. Please provide a file name.")

    name_lower = file_name.lower()
    if name_lower.endswith(".csv"):
        return "csv"
    elif name_lower.endswith(".xlsx"):
        return "xlsx"
    elif name_lower.endswith(".xls"):
        return "xls"
    else:
        ext = file_name.split(".")[-1] if "." in file_name else "unknown"
        raise ValueError(
            f"Unsupported file type '.{ext}'. "
            f"Supported types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )


# ---------------------------------------------------------------------------
# CSV loading
# ---------------------------------------------------------------------------

def _load_csv_from_bytes(raw_bytes: bytes, file_name: str = "") -> LoadResult:
    """Load a CSV from raw bytes."""
    try:
        file_size = len(raw_bytes)

        if file_size == 0:
            return LoadResult(
                success=False,
                error="The uploaded file is empty."
            )

        if file_size > MAX_FILE_SIZE_BYTES:
            limit_mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
            actual_mb = file_size / (1024 * 1024)
            return LoadResult(
                success=False,
                error=(
                    f"File is too large ({actual_mb:.1f} MB). "
                    f"Maximum allowed size is {limit_mb} MB."
                )
            )

        csv_text, encoding_used = _decode_csv(raw_bytes)
        logger.info("Decoded with encoding: %s", encoding_used)

        if "\x00" in csv_text:
            return LoadResult(
                success=False,
                error=(
                    "The file appears to be binary, not a text CSV. "
                    "Please export your data as a plain CSV file."
                )
            )

        df = pd.read_csv(
            io.StringIO(csv_text),
            nrows=MAX_ROWS,
        )

        df.columns = [col.strip() for col in df.columns]
        rows_loaded = len(df)

        if rows_loaded == MAX_ROWS:
            logger.warning(
                "Dataset was truncated at %d rows. "
                "Original file may be larger.",
                MAX_ROWS
            )

        logger.info(
            "Successfully loaded %d rows x %d columns.",
            rows_loaded, len(df.columns)
        )

        return LoadResult(
            success=True,
            data=df,
            encoding_used=encoding_used,
            file_size_bytes=file_size,
            rows_loaded=rows_loaded,
            file_type="csv",
            file_name=file_name,
        )

    except pd.errors.EmptyDataError:
        return LoadResult(
            success=False,
            error="The file contains no data. Please upload a non-empty CSV."
        )
    except pd.errors.ParserError as e:
        return LoadResult(
            success=False,
            error=f"Could not parse the file as CSV: {e}"
        )
    except ValueError as e:
        return LoadResult(
            success=False,
            error=str(e)
        )
    except Exception as e:
        logger.exception("Unexpected error in _load_csv_from_bytes")
        return LoadResult(
            success=False,
            error=f"Unexpected error while loading CSV file: {e}"
        )


# ---------------------------------------------------------------------------
# Excel loading
# ---------------------------------------------------------------------------

def _load_excel_from_bytes(raw_bytes: bytes, file_name: str = "", sheet_name: Optional[Union[str, int]] = 0) -> LoadResult:
    """
    Load an Excel file (.xlsx or .xls) from raw bytes.
    
    Parameters
    ----------
    raw_bytes : bytes
        Raw file content
    file_name : str
        Original filename (for metadata)
    sheet_name : str, int, or None
        Which sheet to read. 0 = first sheet (default). 
        None = read all sheets and concatenate.
    """
    try:
        file_size = len(raw_bytes)

        if file_size == 0:
            return LoadResult(
                success=False,
                error="The uploaded file is empty."
            )

        if file_size > MAX_FILE_SIZE_BYTES:
            limit_mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
            actual_mb = file_size / (1024 * 1024)
            return LoadResult(
                success=False,
                error=(
                    f"File is too large ({actual_mb:.1f} MB). "
                    f"Maximum allowed size is {limit_mb} MB."
                )
            )

        # Use BytesIO to wrap raw bytes for pandas
        excel_buffer = io.BytesIO(raw_bytes)

        # Let pandas auto-detect the engine based on file content
        # instead of forcing it from extension. This handles cases where
        # the extension might not match the actual file format.
        engine = None

        if sheet_name is None:
            # Read all sheets and concatenate
            all_sheets = pd.read_excel(
                excel_buffer,
                sheet_name=None,
                engine=engine,
                nrows=MAX_ROWS,
            )
            dfs = []
            for sheet, df in all_sheets.items():
                if not df.empty:
                    df["__sheet_name__"] = sheet
                    dfs.append(df)
            if not dfs:
                return LoadResult(
                    success=False,
                    error="All sheets in the Excel file are empty."
                )
            df = pd.concat(dfs, ignore_index=True)
            df = df.drop(columns=["__sheet_name__"], errors="ignore")
        else:
            df = pd.read_excel(
                excel_buffer,
                sheet_name=sheet_name,
                engine=engine,
                nrows=MAX_ROWS,
            )

        # Sanitize column names
        df.columns = [str(col).strip() for col in df.columns]

        # Drop completely empty rows and columns
        df = df.dropna(how="all")
        df = df.loc[:, df.columns.notna()]

        rows_loaded = len(df)

        if rows_loaded == 0:
            return LoadResult(
                success=False,
                error="The Excel file contains no valid data rows."
            )

        if rows_loaded == MAX_ROWS:
            logger.warning(
                "Dataset was truncated at %d rows. "
                "Original file may be larger.",
                MAX_ROWS
            )

        logger.info(
            "Successfully loaded Excel: %d rows x %d columns.",
            rows_loaded, len(df.columns)
        )

        return LoadResult(
            success=True,
            data=df,
            encoding_used="utf-8",  # Excel is internally UTF-8
            file_size_bytes=file_size,
            rows_loaded=rows_loaded,
            file_type="xlsx",  # Default; actual format detected by pandas
            file_name=file_name,
        )

    except ImportError as e:
        missing_pkg = "openpyxl" if "openpyxl" in str(e).lower() else "xlrd"
        return LoadResult(
            success=False,
            error=(
                f"Missing required package: {missing_pkg}. "
                f"Install with: pip install {missing_pkg}"
            )
        )
    except pd.errors.EmptyDataError:
        return LoadResult(
            success=False,
            error="The Excel file contains no data."
        )
    except Exception as e:
        logger.exception("Unexpected error in _load_excel_from_bytes")
        return LoadResult(
            success=False,
            error=f"Unexpected error while loading Excel file: {e}"
        )


# ---------------------------------------------------------------------------
# Unified public API
# ---------------------------------------------------------------------------

def load_file(file_input, file_name: str = "") -> LoadResult:
    """
    Load a data file (CSV, XLSX, or XLS) into a Pandas DataFrame.

    Parameters
    ----------
    file_input : str | bytes | file-like
        A file path, raw bytes, or any file-like object
        (including Streamlit's UploadedFile).
    file_name : str
        Original filename. Required for type detection when file_input
        is bytes or file-like. Optional when file_input is a file path.

    Returns
    -------
    LoadResult
        .success     True if loading succeeded.
        .data        DataFrame if success, None otherwise.
        .error       Human-readable error message if failed.
        .encoding_used  Which encoding worked (CSV only).
        .file_size_bytes Raw file size before parsing.
        .rows_loaded    Number of rows in the resulting DataFrame.
        .file_type      Detected file type (csv, xlsx, xls).
        .file_name      Original filename.

    The result also unpacks as a (bool, DataFrame|str) tuple for
    backward compatibility with existing callers.
    """
    try:
        # ---------------------------------------------------------------
        # 1. Read raw bytes
        # ---------------------------------------------------------------
        raw_bytes = _read_bytes(file_input)

        # ---------------------------------------------------------------
        # 2. Determine file name and type
        # ---------------------------------------------------------------
        if isinstance(file_input, str):
            # File path — extract name from path
            detected_name = file_name or file_input.split("/")[-1].split("\\")[-1]
        elif hasattr(file_input, "name"):
            # Streamlit UploadedFile or similar
            detected_name = file_name or file_input.name
        else:
            detected_name = file_name or ""

        if not detected_name:
            return LoadResult(
                success=False,
                error="Cannot determine file type. Please provide a file name."
            )

        # ---------------------------------------------------------------
        # 3. Route to appropriate loader
        # ---------------------------------------------------------------
        file_type = _detect_file_type(detected_name)

        if file_type == "csv":
            return _load_csv_from_bytes(raw_bytes, detected_name)
        else:
            return _load_excel_from_bytes(raw_bytes, detected_name)

    except ValueError as e:
        return LoadResult(success=False, error=str(e))
    except Exception as e:
        logger.exception("Unexpected error in load_file")
        return LoadResult(
            success=False,
            error=f"Unexpected error while loading file: {e}"
        )


# ---------------------------------------------------------------------------
# Backward-compatible alias
# ---------------------------------------------------------------------------

def load_csv(file_input) -> LoadResult:
    """
    Backward-compatible wrapper for CSV files.
    Delegates to load_file with auto-detection.
    
    If file_input is a file-like object without .name (e.g., io.BytesIO
    from old tests), defaults to "data.csv" to preserve backward compatibility.
    """
    file_name = ""
    if isinstance(file_input, str):
        file_name = file_input
    elif hasattr(file_input, "name"):
        file_name = file_input.name
    
    # Backward compatibility: old tests and callers may pass BytesIO
    # without .name. Default to "data.csv" so type detection works.
    if not file_name:
        file_name = "data.csv"

    result = load_file(file_input, file_name)
    # Ensure backward compatibility: if Excel was passed to load_csv,
    # still return the result (load_file handles it)
    return result