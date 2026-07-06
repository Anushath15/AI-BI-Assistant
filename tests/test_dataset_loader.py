"""
tests/test_dataset_loader.py

Unit tests for the unified DatasetLoadPipeline and data_loader Excel support.

Run with:
    pytest tests/test_dataset_loader.py -v
"""

import io
import pytest
import pandas as pd

from core.dataset_loader import DatasetLoadPipeline, PipelineResult, update_session_state
from core.data_loader import load_file, LoadResult, SUPPORTED_EXTENSIONS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_csv_bytes(content: str, encoding: str = "utf-8") -> bytes:
    return content.encode(encoding)


def make_excel_bytes(df: pd.DataFrame, engine: str = "openpyxl") -> bytes:
    """Create an in-memory Excel file from a DataFrame."""
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine=engine)
    buf.seek(0)
    return buf.read()


VALID_CSV = "Name,Sales,Date\nAlice,100,2024-01-01\nBob,200,2024-01-02\n"


# ---------------------------------------------------------------------------
# Test data fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame({
        "Region": ["West", "East", "Central"],
        "Sales": [500.0, 200.0, 150.0],
        "Profit": [120.0, -30.0, 45.0],
    })


# ---------------------------------------------------------------------------
# load_file -- CSV support (existing behavior preserved)
# ---------------------------------------------------------------------------

class TestLoadFileCsv:

    def test_load_csv_from_bytes(self):
        raw = make_csv_bytes(VALID_CSV)
        result = load_file(io.BytesIO(raw), file_name="test.csv")
        assert result.success is True
        assert result.file_type == "csv"
        assert result.rows_loaded == 2
        assert list(result.data.columns) == ["Name", "Sales", "Date"]

    def test_load_csv_empty_file(self):
        result = load_file(io.BytesIO(b""), file_name="empty.csv")
        assert result.success is False
        assert "empty" in result.error.lower()

    def test_load_csv_unsupported_extension(self):
        result = load_file(io.BytesIO(b"abc"), file_name="data.txt")
        assert result.success is False
        assert "unsupported" in result.error.lower()

    def test_load_csv_no_filename(self):
        """
        load_file() requires a file name for type detection.
        load_csv() has backward-compat default, but load_file() is strict.
        """
        result = load_file(io.BytesIO(b"a,b\n1,2\n"))
        assert result.success is False
        assert "file name" in result.error.lower() or "cannot determine" in result.error.lower()


# ---------------------------------------------------------------------------
# load_file -- Excel support (new)
# ---------------------------------------------------------------------------

class TestLoadFileExcel:

    def test_load_xlsx_from_bytes(self, sample_df):
        raw = make_excel_bytes(sample_df)
        result = load_file(io.BytesIO(raw), file_name="sales.xlsx")
        assert result.success is True
        assert result.file_type == "xlsx"
        assert result.rows_loaded == 3
        assert "Region" in result.data.columns
        assert "Sales" in result.data.columns

    def test_load_xls_from_bytes(self, sample_df):
        """
        Pandas auto-detects engine from file CONTENT, not extension.
        Even if we name it .xls, openpyxl-generated content will be read
        successfully because pandas ignores the extension.
        """
        raw = make_excel_bytes(sample_df)
        result = load_file(io.BytesIO(raw), file_name="sales.xls")
        # Pandas auto-detects the actual format, so this succeeds
        assert result.success is True
        assert result.rows_loaded == 3
        assert "Region" in result.data.columns

    def test_load_excel_empty_file(self):
        result = load_file(io.BytesIO(b""), file_name="empty.xlsx")
        assert result.success is False
        assert "empty" in result.error.lower()

    def test_load_excel_file_too_large(self):
        big_content = b"a,b\n" + b"1,2\n" * (50 * 1024 * 1024 // 4)
        result = load_file(io.BytesIO(big_content), file_name="big.xlsx")
        assert result.success is False
        assert "large" in result.error.lower()


# ---------------------------------------------------------------------------
# DatasetLoadPipeline -- unified pipeline
# ---------------------------------------------------------------------------

class TestDatasetLoadPipeline:

    def test_pipeline_csv_success(self):
        raw = make_csv_bytes(VALID_CSV)
        pipeline = DatasetLoadPipeline()
        result = pipeline.run(io.BytesIO(raw), file_name="test.csv")

        assert result.success is True
        assert result.df is not None
        assert result.profile is not None
        assert result.schema is not None
        assert result.dataset_name == "test.csv"
        assert result.file_type == "csv"
        assert result.rows_loaded == 2
        assert result.kpis is not None

    def test_pipeline_excel_success(self, sample_df):
        raw = make_excel_bytes(sample_df)
        pipeline = DatasetLoadPipeline()
        result = pipeline.run(io.BytesIO(raw), file_name="sales.xlsx")

        assert result.success is True
        assert result.df is not None
        assert result.profile is not None
        assert result.schema is not None
        assert result.dataset_name == "sales.xlsx"
        assert result.file_type == "xlsx"

    def test_pipeline_failure_returns_error(self):
        pipeline = DatasetLoadPipeline()
        result = pipeline.run(io.BytesIO(b""), file_name="empty.csv")

        assert result.success is False
        assert result.error is not None
        assert result.df is None
        assert result.profile is None

    def test_pipeline_custom_label(self, sample_df):
        raw = make_excel_bytes(sample_df)
        pipeline = DatasetLoadPipeline()
        result = pipeline.run(
            io.BytesIO(raw),
            file_name="sales.xlsx",
            dataset_label="Q1 Sales 2025",
        )
        assert result.dataset_name == "Q1 Sales 2025"

    def test_pipeline_kpis_populated(self, sample_df):
        raw = make_excel_bytes(sample_df)
        pipeline = DatasetLoadPipeline()
        result = pipeline.run(io.BytesIO(raw), file_name="sales.xlsx")
        assert len(result.kpis) > 0
        # Should have Total Sales at minimum
        assert any("Sales" in k for k in result.kpis.keys())


# ---------------------------------------------------------------------------
# PipelineResult
# ---------------------------------------------------------------------------

class TestPipelineResult:

    def test_success_repr(self):
        result = PipelineResult(success=True, dataset_name="Test", rows_loaded=100)
        assert "success=True" in repr(result)
        assert "Test" in repr(result)

    def test_failure_repr(self):
        result = PipelineResult(success=False, error="Bad file")
        assert "success=False" in repr(result)
        assert "Bad file" in repr(result)


# ---------------------------------------------------------------------------
# update_session_state
# ---------------------------------------------------------------------------

class TestUpdateSessionState:

    def test_updates_all_keys(self, sample_df):
        raw = make_excel_bytes(sample_df)
        pipeline = DatasetLoadPipeline()
        result = pipeline.run(io.BytesIO(raw), file_name="sales.xlsx")

        # Use a dict subclass that supports both bracket and attribute access
        # to simulate Streamlit session state behavior in tests
        class MockSessionState(dict):
            def __setattr__(self, key, value):
                self[key] = value
            def __getattr__(self, key):
                return self.get(key)

        mock_state = MockSessionState()
        update_session_state(mock_state, result)

        assert mock_state["df"] is not None
        assert mock_state["profile"] is not None
        assert mock_state["business_schema"] is not None
        assert mock_state["loaded_dataset"] == "sales.xlsx"
        assert len(mock_state["kpis"]) > 0
        assert mock_state["session"] is not None
        assert mock_state["context"] is not None

    def test_does_nothing_on_failure(self):
        mock_state = {"df": "original"}
        result = PipelineResult(success=False, error="fail")
        update_session_state(mock_state, result)
        assert mock_state["df"] == "original"