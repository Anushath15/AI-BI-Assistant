 
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
 
 
# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
 
def load_csv(file_input) -> LoadResult:
    """
    Load a CSV file into a Pandas DataFrame.
 
    Parameters
    ----------
    file_input : str | bytes | file-like
        A file path, raw bytes, or any file-like object
        (including Streamlit's UploadedFile).
 
    Returns
    -------
    LoadResult
        .success     True if loading succeeded.
        .data        DataFrame if success, None otherwise.
        .error       Human-readable error message if failed.
        .encoding_used  Which encoding worked.
        .file_size_bytes Raw file size before parsing.
        .rows_loaded    Number of rows in the resulting DataFrame.
 
    The result also unpacks as a (bool, DataFrame|str) tuple for
    backward compatibility with existing callers.
    """
    try:
        # ---------------------------------------------------------------
        # 1. Read raw bytes
        # ---------------------------------------------------------------
        raw_bytes = _read_bytes(file_input)
        file_size = len(raw_bytes)
 
        logger.info("Received file input: %d bytes", file_size)
 
        # ---------------------------------------------------------------
        # 2. Enforce size limit
        # ---------------------------------------------------------------
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
 
        # ---------------------------------------------------------------
        # 3. Decode bytes to string
        # ---------------------------------------------------------------
        csv_text, encoding_used = _decode_csv(raw_bytes)
        logger.info("Decoded with encoding: %s", encoding_used)
 
        # ---------------------------------------------------------------
        # 4. Reject binary files masquerading as CSV
        #    Null bytes are never present in real text CSV files.
        #    Their presence means the file is binary (e.g. an Excel
        #    .xlsx saved with a .csv extension, or a PDF, etc.).
        # ---------------------------------------------------------------
        if "\x00" in csv_text:
            return LoadResult(
                success=False,
                error=(
                    "The file appears to be binary, not a text CSV. "
                    "Please export your data as a plain CSV file."
                )
            )
 
        # ---------------------------------------------------------------
        # 5. Parse CSV
        # ---------------------------------------------------------------
        df = pd.read_csv(
            io.StringIO(csv_text),
            nrows=MAX_ROWS,
        )
 
        # ---------------------------------------------------------------
        # 6. Sanitise column names
        #    Strip leading/trailing whitespace from column names.
        #    "  Sales " and "Sales" should be the same column.
        # ---------------------------------------------------------------
        df.columns = [col.strip() for col in df.columns]
 
        # ---------------------------------------------------------------
        # 7. Truncation warning
        # ---------------------------------------------------------------
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
        logger.exception("Unexpected error in load_csv")
        return LoadResult(
            success=False,
            error=f"Unexpected error while loading file: {e}"
        )
 