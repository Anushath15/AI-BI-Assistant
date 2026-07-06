"""
ui/upload_components.py

Upload-related UI components for the AI BI Assistant.
All presentation logic lives here; data logic lives in core/upload_manager.
"""

import streamlit as st
from typing import Dict, Optional, Any

from core.upload_manager import FilePreview
from core.excel_loader import ExcelInfo
from models.dataset_profile import DatasetProfile


# ------------------------------------------------------------------
# Upload Area
# ------------------------------------------------------------------
def render_upload_area() -> Optional[Any]:
    """Professional drag-and-drop upload area. Returns UploadedFile or None."""
    st.markdown(
        """
        <style>
        .upload-zone {
            border: 2px dashed #CBD5E1;
            border-radius: 16px;
            padding: 36px 24px;
            text-align: center;
            background: linear-gradient(180deg, #F8FAFC 0%, #F1F5F9 100%);
            margin-bottom: 8px;
            transition: all 0.3s ease;
        }
        .upload-zone:hover {
            border-color: #3B82F6;
            background: #EFF6FF;
        }
        .upload-title {
            font-size: 15px;
            font-weight: 600;
            color: #374151;
            margin-bottom: 4px;
        }
        .upload-subtitle {
            font-size: 13px;
            color: #6B7280;
            margin-bottom: 12px;
        }
        .upload-hint {
            font-size: 11px;
            color: #9CA3AF;
            margin-top: 8px;
            text-align: center;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="upload-zone">
            <div style="font-size: 36px; margin-bottom: 8px;">📂</div>
            <div class="upload-title">Upload Dataset</div>
            <div class="upload-subtitle">Drag & Drop your dataset here</div>
            <div style="color: #9CA3AF; font-size: 12px;">or</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Browse Files",
        type=["csv", "xlsx", "xls"],
        label_visibility="collapsed",
        key="dataset_uploader",
    )

    st.markdown(
        """
        <div class="upload-hint">
            Supports: <strong>CSV</strong> • <strong>XLSX</strong> • <strong>XLS</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    return uploaded_file


# ------------------------------------------------------------------
# File Preview
# ------------------------------------------------------------------
def render_file_preview(preview: FilePreview):
    """Show filename, size, type, sheets, and estimated rows before processing."""
    size_str = _format_bytes(preview.size_bytes)

    sheet_line = ""
    if preview.sheet_count is not None:
        label = "Sheet" if preview.sheet_count == 1 else "Sheets"
        sheet_line = f'<div>📑 <strong>{label}:</strong> {preview.sheet_count}</div>'

    rows_line = ""
    if preview.estimated_rows is not None:
        rows_line = f'<div>📊 <strong>Estimated Rows:</strong> {preview.estimated_rows:,}</div>'

    st.markdown(
        f"""
        <div style="
            background: white;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            padding: 18px;
            margin: 12px 0;
        ">
            <div style="font-weight: 700; font-size: 15px; color: #111827; margin-bottom: 10px;">
                {preview.filename}
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 13px; color: #4B5563;">
                <div>💾 <strong>Size:</strong> {size_str}</div>
                <div>📄 <strong>Type:</strong> {preview.extension}</div>
                {sheet_line}
                {rows_line}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------
# Sheet Selector
# ------------------------------------------------------------------
def render_sheet_selector(excel_info: ExcelInfo, key: str = "sheet_selector") -> str:
    """Dropdown for Excel sheet selection. Returns selected sheet name."""
    if len(excel_info.sheet_names) <= 1:
        return excel_info.selected_sheet

    st.markdown('<div style="margin-top: 12px;"></div>', unsafe_allow_html=True)
    selected = st.selectbox(
        "📑 Select Sheet",
        excel_info.sheet_names,
        index=0,
        key=key,
    )
    return selected


# ------------------------------------------------------------------
# Header Selector
# ------------------------------------------------------------------
def render_header_selector(detected_row: int, max_rows: int = 10, key: str = "header_selector") -> int:
    """Dropdown to confirm or override the detected header row."""
    options = [f"Row {i}" for i in range(max_rows)]
    safe_index = min(detected_row, max_rows - 1)

    st.markdown('<div style="margin-top: 12px;"></div>', unsafe_allow_html=True)
    selected = st.selectbox(
        "🔍 Detected Header Row",
        options,
        index=safe_index,
        key=key,
        help="If detection is wrong, select the correct header row manually.",
    )
    return int(selected.replace("Row ", ""))


# ------------------------------------------------------------------
# Type Override
# ------------------------------------------------------------------
def render_type_override(profile: DatasetProfile, key_prefix: str = "type_override") -> Dict[str, str]:
    """
    Show detected types and let the user override them.
    Returns a dict of {column: target_type} for non-Auto selections.
    """
    st.markdown("##### 🎛️ Column Type Override")
    st.caption("Override detected types if needed. Select 'Auto' to keep the detected type.")

    type_options = ["Auto", "string", "integer", "float", "boolean", "datetime", "category"]
    overrides = {}

    cols = st.columns(2)
    for i, col_name in enumerate(profile.column_names):
        detected = profile.data_types.get(col_name, "object")
        display = detected.replace("object", "string").replace("float64", "float").replace("int64", "integer")

        with cols[i % 2]:
            selected = st.selectbox(
                f"{col_name}",
                type_options,
                index=0,
                key=f"{key_prefix}_{col_name}",
                help=f"Detected: {display}",
            )
            if selected != "Auto":
                overrides[col_name] = selected

    return overrides


# ------------------------------------------------------------------
# Upload History
# ------------------------------------------------------------------
def render_upload_history(history: Dict[str, dict]) -> Optional[str]:
    """Dropdown of previously uploaded datasets. Returns selected name or None."""
    if not history:
        return None

    st.divider()
    st.markdown(
        '<div class="section-label">Upload History</div>',
        unsafe_allow_html=True,
    )

    names = list(history.keys())
    selected = st.selectbox(
        "Current Dataset",
        names,
        key="upload_history_selector",
    )
    return selected


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def _format_bytes(size: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"