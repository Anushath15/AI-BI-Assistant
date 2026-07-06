"""
core/upload_manager.py

Enterprise upload pipeline orchestrator.
Handles validation, preview, header detection, type override,
cleaning, profiling, and business-schema generation.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple

import pandas as pd

from core.data_loader import load_csv
from core.excel_loader import get_excel_info, load_excel_sheet
from core.header_detector import detect_header_row, apply_header
from core.type_converter import apply_type_overrides
from core.data_cleaner import DataCleaner
from core.data_profiler import DataProfiler
from core.business_knowledge import BusinessKnowledgeBuilder
from utils.logger import get_logger

logger = get_logger(__name__)

MAX_UPLOAD_SIZE_BYTES = 50 * 1024 * 1024


@dataclass
class FilePreview:
    filename: str
    size_bytes: int
    extension: str
    sheet_count: Optional[int] = None
    estimated_rows: Optional[int] = None


@dataclass
class UploadPipelineResult:
    success: bool
    df: Optional[pd.DataFrame] = None
    profile: Optional[Any] = None
    schema: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class UploadManager:
    """
    Upload → Validate → Preview → Sheet Select → Header Detect
    → Type Override → Clean → Profile → Schema
    """

    def __init__(self):
        self.data_cleaner = DataCleaner()
        self.data_profiler = DataProfiler()
        self.knowledge_builder = BusinessKnowledgeBuilder()

    # ------------------------------------------------------------------
    # Stage 1: Validation
    # ------------------------------------------------------------------
    def validate_file(
        self, uploaded_file
    ) -> Tuple[bool, Optional[str], Optional[FilePreview]]:
        if uploaded_file is None:
            return False, "No file uploaded.", None

        filename = uploaded_file.name
        size = uploaded_file.size
        ext = filename.split(".")[-1].lower()

        if size == 0:
            return False, "The uploaded file is empty.", None

        if size > MAX_UPLOAD_SIZE_BYTES:
            limit_mb = MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
            actual_mb = size / (1024 * 1024)
            return (
                False,
                f"File is too large ({actual_mb:.1f} MB). Maximum allowed is {limit_mb} MB.",
                None,
            )

        if ext not in ("csv", "xlsx", "xls"):
            return (
                False,
                f"Unsupported extension '.{ext}'. Supported: CSV, XLSX, XLS.",
                None,
            )

        preview = FilePreview(
            filename=filename,
            size_bytes=size,
            extension=ext.upper(),
        )

        try:
            if ext in ("xlsx", "xls"):
                info = get_excel_info(uploaded_file)
                if info.password_protected:
                    return (
                        False,
                        "This Excel file is password-protected. Please remove the password and try again.",
                        None,
                    )
                if info.error:
                    return False, info.error, None
                preview.sheet_count = len(info.sheet_names)
            else:
                uploaded_file.seek(0)
                content = uploaded_file.read()
                preview.estimated_rows = content.count(b"\n")
                uploaded_file.seek(0)
        except Exception as e:
            logger.warning("Preview metadata extraction failed: %s", e)

        return True, None, preview

    # ------------------------------------------------------------------
    # Stage 2: Raw Load
    # ------------------------------------------------------------------
    def load_raw(
        self,
        uploaded_file,
        header_row: int = 0,
        sheet_name: Optional[str] = None,
    ) -> Tuple[bool, Optional[pd.DataFrame], Optional[str]]:
        ext = uploaded_file.name.split(".")[-1].lower()

        try:
            if ext == "csv":
                result = load_csv(uploaded_file)
                if result.success:
                    return True, result.data, None
                return False, None, result.error

            elif ext in ("xlsx", "xls"):
                df = load_excel_sheet(
                    uploaded_file,
                    sheet_name=sheet_name or 0,
                    header_row=header_row,
                )
                return True, df, None

            else:
                return False, None, f"Unsupported extension: {ext}"

        except Exception as e:
            logger.exception("Raw load failed")
            return False, None, f"Failed to read file: {e}"

    # ------------------------------------------------------------------
    # Stage 3: Header
    # ------------------------------------------------------------------
    def detect_header(self, df_raw: pd.DataFrame) -> int:
        return detect_header_row(df_raw)

    def apply_header(self, df_raw: pd.DataFrame, header_row: int) -> pd.DataFrame:
        return apply_header(df_raw, header_row)

    # ------------------------------------------------------------------
    # Stage 4: Type Override
    # ------------------------------------------------------------------
    def apply_overrides(
        self, df: pd.DataFrame, overrides: Dict[str, str]
    ) -> Tuple[pd.DataFrame, list]:
        return apply_type_overrides(df, overrides)

    # ------------------------------------------------------------------
    # Full Pipeline
    # ------------------------------------------------------------------
    def run_pipeline(
        self,
        uploaded_file,
        header_row: Optional[int] = None,
        sheet_name: Optional[str] = None,
        type_overrides: Optional[Dict[str, str]] = None,
    ) -> UploadPipelineResult:
        # Validate
        ok, error, preview = self.validate_file(uploaded_file)
        if not ok:
            return UploadPipelineResult(success=False, error=error)

        # Load raw (no header assumption)
        ok, df_raw, error = self.load_raw(
            uploaded_file, header_row=0, sheet_name=sheet_name
        )
        if not ok:
            return UploadPipelineResult(success=False, error=error)

        # Header detection
        if header_row is None:
            header_row = self.detect_header(df_raw)

        df = self.apply_header(df_raw, header_row)

        if df.empty or len(df.columns) == 0:
            return UploadPipelineResult(
                success=False,
                error="No data found after header detection. The file may be empty or missing headers.",
            )

        # Check for completely auto-named columns (failed header detection)
        auto_named = sum(1 for c in df.columns if c.startswith("Column_"))
        if auto_named == len(df.columns):
            return UploadPipelineResult(
                success=False,
                error="Could not detect valid headers. Please check the file format.",
            )

        # Type overrides
        if type_overrides:
            df, errors = self.apply_overrides(df, type_overrides)
            if errors:
                return UploadPipelineResult(
                    success=False,
                    error="Type conversion failed:\n• " + "\n• ".join(errors),
                )

        # Clean
        df_cleaned, clean_report = self.data_cleaner.clean(df)

        # Profile
        profile = self.data_profiler.profile(df_cleaned)

        # Business schema
        schema = self.knowledge_builder.build(profile, preview.filename)

        metadata = {
            "filename": preview.filename,
            "size_bytes": preview.size_bytes,
            "extension": preview.extension,
            "sheet_count": preview.sheet_count,
            "estimated_rows": preview.estimated_rows,
            "header_row": header_row,
            "sheet_name": sheet_name,
            "type_overrides": type_overrides or {},
            "clean_report": clean_report,
        }

        return UploadPipelineResult(
            success=True,
            df=df_cleaned,
            profile=profile,
            schema=schema,
            metadata=metadata,
        )