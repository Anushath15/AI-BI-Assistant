"""
core/dataset_loader.py

Unified dataset loading pipeline.

This module provides a single entry point for loading datasets from ANY source
(registry files OR user uploads) and running them through the complete
preprocessing pipeline:

    Raw File -> DataLoader -> DataCleaner -> DataProfiler -> BusinessKnowledgeBuilder

This eliminates duplicate loading logic between Workflow A (registry) and
Workflow B (upload).
"""

import pandas as pd
from typing import Optional, Union

from core.data_loader import load_file, LoadResult
from core.data_cleaner import DataCleaner
from core.data_profiler import DataProfiler
from core.business_knowledge import BusinessKnowledgeBuilder
from core.session_manager import SessionManager
from core.conversation_context import ConversationContext
from models.dataset_profile import DatasetProfile
from models.business_schema import BusinessSchema
from utils.logger import get_logger

logger = get_logger(__name__)


class DatasetLoadPipeline:
    """
    Orchestrates the complete dataset loading and preparation pipeline.
    
    Usage:
        pipeline = DatasetLoadPipeline()
        result = pipeline.run(file_input, file_name="sales.csv")
        if result.success:
            # result contains: df, profile, schema, kpis
            pass
    """

    def __init__(self):
        self.cleaner = DataCleaner()
        self.profiler = DataProfiler()
        self.knowledge_builder = BusinessKnowledgeBuilder()

    def run(
        self,
        file_input,
        file_name: str = "",
        dataset_label: str = "",
    ) -> "PipelineResult":
        """
        Run the full pipeline on a file input.

        Parameters
        ----------
        file_input : str | bytes | file-like
            File path, raw bytes, or Streamlit UploadedFile.
        file_name : str
            Original filename (for type detection).
        dataset_label : str
            Display name for the dataset (e.g., "Sales 2025").

        Returns
        -------
        PipelineResult
        """
        # Step 1: Load raw file
        load_result = load_file(file_input, file_name)
        if not load_result.success:
            return PipelineResult(
                success=False,
                error=load_result.error,
            )

        raw_df = load_result.data
        actual_name = dataset_label or load_result.file_name or "Dataset"

        # Step 2: Clean
        cleaned_df, clean_report = self.cleaner.clean(raw_df)

        # Step 3: Profile
        profile = self.profiler.profile(cleaned_df)

        # Step 4: Build business knowledge
        schema = self.knowledge_builder.build(profile, actual_name)

        # Step 5: Compute KPIs
        kpis = self._compute_kpis(cleaned_df, schema)

        logger.info(
            "Pipeline complete: %s | %d rows | %d cols | %d kpis",
            actual_name, profile.rows, profile.columns, len(kpis)
        )

        return PipelineResult(
            success=True,
            df=cleaned_df,
            profile=profile,
            schema=schema,
            kpis=kpis,
            dataset_name=actual_name,
            file_type=load_result.file_type,
            file_size=load_result.file_size_bytes,
            rows_loaded=load_result.rows_loaded,
            clean_report=clean_report,
        )

    def _compute_kpis(self, df: pd.DataFrame, schema: BusinessSchema) -> dict:
        """
        Compute KPIs dynamically based on available columns.
        Extracted from app.py to keep loading logic centralized.
        """
        kpis = {}
        try:
            numeric_cols = df.select_dtypes(include="number").columns.tolist()

            if numeric_cols:
                first_num = numeric_cols[0]
                kpis[f"Total {first_num}"] = f"${df[first_num].sum():,.0f}"

                if len(numeric_cols) > 1:
                    second_num = numeric_cols[1]
                    kpis[f"Total {second_num}"] = f"${df[second_num].sum():,.0f}"

            id_cols = [c for c in df.columns if any(kw in c.lower() for kw in ["id", "key", "code"])]
            if id_cols:
                kpis["Records"] = f"{df[id_cols[0]].nunique():,}"

            name_cols = [c for c in df.columns if "name" in c.lower()]
            if name_cols:
                kpis["Unique Names"] = f"{df[name_cols[0]].nunique():,}"

            categorical_cols = df.select_dtypes(include="object").columns.tolist()
            if categorical_cols and numeric_cols:
                top_dim = categorical_cols[0]
                top_num = numeric_cols[0]
                top = df.groupby(top_dim)[top_num].sum().idxmax()
                kpis[f"Top {top_dim}"] = top

                if len(categorical_cols) > 1:
                    second_dim = categorical_cols[1]
                    top2 = df.groupby(second_dim)[top_num].sum().idxmax()
                    kpis[f"Top {second_dim}"] = top2

        except Exception as e:
            logger.warning("KPI computation skipped: %s", e)

        return kpis


class PipelineResult:
    """
    Result of running DatasetLoadPipeline.
    
    Attributes
    ----------
    success : bool
    df : pd.DataFrame | None
    profile : DatasetProfile | None
    schema : BusinessSchema | None
    kpis : dict
    dataset_name : str
    file_type : str | None
    file_size : int | None
    rows_loaded : int | None
    clean_report : dict | None
    error : str | None
    """

    def __init__(
        self,
        success: bool,
        df: Optional[pd.DataFrame] = None,
        profile: Optional[DatasetProfile] = None,
        schema: Optional[BusinessSchema] = None,
        kpis: Optional[dict] = None,
        dataset_name: str = "",
        file_type: Optional[str] = None,
        file_size: Optional[int] = None,
        rows_loaded: Optional[int] = None,
        clean_report: Optional[dict] = None,
        error: Optional[str] = None,
    ):
        self.success = success
        self.df = df
        self.profile = profile
        self.schema = schema
        self.kpis = kpis or {}
        self.dataset_name = dataset_name
        self.file_type = file_type
        self.file_size = file_size
        self.rows_loaded = rows_loaded
        self.clean_report = clean_report
        self.error = error

    def __repr__(self) -> str:
        if self.success:
            return (
                f"PipelineResult(success=True, name={self.dataset_name!r}, "
                f"rows={self.rows_loaded}, cols={len(self.df.columns) if self.df is not None else 0})"
            )
        return f"PipelineResult(success=False, error={self.error!r})"


def update_session_state(
    st_session_state,
    pipeline_result: PipelineResult,
) -> None:
    
    if not pipeline_result.success:
        return

    st_session_state["df"] = pipeline_result.df
    st_session_state["profile"] = pipeline_result.profile
    st_session_state["business_schema"] = pipeline_result.schema
    st_session_state["kpis"] = pipeline_result.kpis
    st_session_state["loaded_dataset"] = pipeline_result.dataset_name
    
    # Reset chat and context for new dataset
    st_session_state["session"] = SessionManager()
    st_session_state["context"] = ConversationContext()