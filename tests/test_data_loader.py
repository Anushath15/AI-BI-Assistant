import io
import pytest
import pandas as pd
 
from data_loader import (
    load_csv,
    LoadResult,
    MAX_FILE_SIZE_BYTES,
    MAX_ROWS,
)
 
 
# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
 
def make_csv_bytes(content: str, encoding: str = "utf-8") -> bytes:
    return content.encode(encoding)
 
 
def make_file_like(content: str, encoding: str = "utf-8") -> io.BytesIO:
    return io.BytesIO(content.encode(encoding))
 
 
VALID_CSV = "Name,Sales,Date\nAlice,100,2024-01-01\nBob,200,2024-01-02\n"
 
 
# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------
 
class TestLoadCsvSuccess:
 
    def test_returns_load_result(self):
        result = load_csv(make_file_like(VALID_CSV))
        assert isinstance(result, LoadResult)
 
    def test_success_is_true(self):
        result = load_csv(make_file_like(VALID_CSV))
        assert result.success is True
 
    def test_data_is_dataframe(self):
        result = load_csv(make_file_like(VALID_CSV))
        assert isinstance(result.data, pd.DataFrame)
 
    def test_correct_row_count(self):
        result = load_csv(make_file_like(VALID_CSV))
        assert result.rows_loaded == 2
 
    def test_correct_columns(self):
        result = load_csv(make_file_like(VALID_CSV))
        assert list(result.data.columns) == ["Name", "Sales", "Date"]
 
    def test_encoding_recorded(self):
        result = load_csv(make_file_like(VALID_CSV))
        assert result.encoding_used is not None
 
    def test_file_size_recorded(self):
        raw = make_file_like(VALID_CSV)
        result = load_csv(raw)
        assert result.file_size_bytes == len(VALID_CSV.encode("utf-8"))
 
    def test_tuple_unpacking_success(self):
        """Backward compatibility: success, result = load_csv(...)"""
        success, data = load_csv(make_file_like(VALID_CSV))
        assert success is True
        assert isinstance(data, pd.DataFrame)
 
    def test_column_names_stripped(self):
        csv_with_spaces = " Name , Sales , Date \nAlice,100,2024-01-01\n"
        result = load_csv(make_file_like(csv_with_spaces))
        assert list(result.data.columns) == ["Name", "Sales", "Date"]
 
    def test_latin1_encoding(self):
        csv_latin1 = "Produit,Prix\ncafé,10\nthé,5\n"
        result = load_csv(make_file_like(csv_latin1, encoding="latin-1"))
        assert result.success is True
        assert result.encoding_used == "latin-1"
 
    def test_utf8_bom_encoding(self):
        """Excel often saves CSVs with a UTF-8 BOM."""
        csv_bom = VALID_CSV.encode("utf-8-sig")
        result = load_csv(io.BytesIO(csv_bom))
        assert result.success is True
 
 
# ---------------------------------------------------------------------------
# Failure cases
# ---------------------------------------------------------------------------
 
class TestLoadCsvFailures:
 
    def test_empty_file(self):
        result = load_csv(io.BytesIO(b""))
        assert result.success is False
        assert "empty" in result.error.lower()
 
    def test_tuple_unpacking_failure(self):
        """Backward compatibility: success, error = load_csv(...) on fail"""
        success, error = load_csv(io.BytesIO(b""))
        assert success is False
        assert isinstance(error, str)
 
    def test_file_too_large(self):
        big_content = b"a,b\n" + b"1,2\n" * (MAX_FILE_SIZE_BYTES // 4)
        result = load_csv(io.BytesIO(big_content))
        assert result.success is False
        assert "large" in result.error.lower()
 
    def test_invalid_csv_structure(self):
        garbage = io.BytesIO(b"\x00\x01\x02\x03" * 100)
        result = load_csv(garbage)
        # May fail on decode or parse — either way must be a clean failure
        assert result.success is False
        assert result.error is not None
 
    def test_headers_only_no_data(self):
        headers_only = "Name,Sales,Date\n"
        result = load_csv(make_file_like(headers_only))
        # pd reads this as 0 rows — valid load, just empty
        assert result.success is True
        assert result.rows_loaded == 0
 
    def test_error_is_none_on_success(self):
        result = load_csv(make_file_like(VALID_CSV))
        assert result.error is None
 
    def test_data_is_none_on_failure(self):
        result = load_csv(io.BytesIO(b""))
        assert result.data is None
 
 
# ---------------------------------------------------------------------------
# repr
# ---------------------------------------------------------------------------
 
class TestLoadResultRepr:
 
    def test_success_repr(self):
        result = load_csv(make_file_like(VALID_CSV))
        assert "success=True" in repr(result)
        assert "rows=2" in repr(result)
 
    def test_failure_repr(self):
        result = load_csv(io.BytesIO(b""))
        assert "success=False" in repr(result)
 