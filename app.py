import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ---------------------------
# Streamlit Configuration
# ---------------------------
st.set_page_config(
    page_title="AI BI Assistant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ✅ FIX 1: load_dotenv after page config
from dotenv import load_dotenv
load_dotenv()

# ---------------------------
# UI
# ---------------------------
from ui.styles import apply_global_styles

# ✅ FIX 2 & 8: Check if new UI components exist, fallback to old
try:
    from ui.components import (
        render_app_header,
        render_empty_state,
        render_insight_card,
        render_kpi_card,
        render_planning_error,
        render_section_label,
        render_sidebar_metric,
    )
    USE_NEW_UI = True
except ImportError:
    USE_NEW_UI = False

if USE_NEW_UI:
    from ui.styles import apply_global_styles
    apply_global_styles()
else:
    apply_global_styles()

# ---------------------------
# Core Modules
# ---------------------------
from core.ai_client import AIClient
from core.analysis_engine import AnalysisEngine
from core.business_knowledge import BusinessKnowledgeBuilder
from core.chart_engine import ChartEngine
from core.command_validator import CommandValidator
from core.conversation_context import ConversationContext
from core.data_cleaner import DataCleaner
from core.data_profiler import DataProfiler
from core.dataset_registry import DatasetRegistry
from core.explanation_engine import ExplanationEngine
from core.forecast_engine import ForecastEngine
from core.prompt_builder import PromptBuilder
from core.session_manager import ChatEntry, SessionManager

# ✅ NEW: Enterprise upload pipeline modules
from core.upload_manager import UploadManager, UploadPipelineResult
from core.excel_loader import get_excel_info
from ui.upload_components import (
    render_upload_area,
    render_file_preview,
    render_sheet_selector,
    render_header_selector,
    render_type_override,
    render_upload_history,
)

# ------------------------------------------------------------------
# Session state
# ------------------------------------------------------------------

for key, default in {
    "df": None, "profile": None,
    "session": None, "context": None,
    "business_schema": None, "loaded_dataset": None,
    "kpis": {},
    "upload_history": {},          # ✅ Feature 3: Upload History cache
    "upload_preview": None,        # ✅ Feature 4: File preview state
    "upload_excel_info": None,     # ✅ Feature 1: Excel sheet info
    "upload_header_row": None,     # ✅ Feature 6: Header row state
    "upload_overrides": {},        # ✅ Feature 5: Type overrides state
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

if st.session_state.session is None:
    st.session_state.session = SessionManager()
if st.session_state.context is None:
    st.session_state.context = ConversationContext()

# ------------------------------------------------------------------
# KPI computation (kept for backward compatibility)
# ------------------------------------------------------------------

def compute_kpis(df: pd.DataFrame, schema) -> dict:
    """
    Compute KPIs dynamically based on available columns.
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
        st.warning(f"KPI computation skipped: {e}")
    return kpis


# ==================================================================
# SIDEBAR — Dataset Selection & Upload (ALL 10 FEATURES)
# ==================================================================

with st.sidebar:
    # ---------------- Logo ----------------
    if USE_NEW_UI:
        st.markdown("""
            <div style="padding:1.25rem 0 1.25rem 0;border-bottom:1px solid #1F2937;
                        margin-bottom:1.25rem;">
                <div style="display:flex;align-items:center;gap:0.6rem;">
                    <svg width="28" height="28" viewBox="0 0 32 32" fill="none">
                        <rect width="32" height="32" rx="8" fill="#2563EB"/>
                        <path d="M8 22L13 14L18 17L23 10L27 16" stroke="white"
                              stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <div>
                        <div style="font-size:0.95rem;font-weight:700;color:#F9FAFB;
                                    letter-spacing:-0.01em;">AI BI Assistant</div>
                        <div style="font-size:0.65rem;color:#6B7280;text-transform:uppercase;
                                    letter-spacing:0.06em;">Enterprise Platform</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="sidebar-logo">
                <div class="sidebar-logo-text">⬡ AI BI Assistant</div>
                <div class="sidebar-logo-sub">Enterprise Intelligence Platform</div>
            </div>
        """, unsafe_allow_html=True)

    # ================================================================
    # SECTION: Choose Dataset
    # ================================================================
    if USE_NEW_UI:
        render_section_label("Choose Dataset")
    else:
        st.markdown('<div class="section-label">Choose Dataset</div>', unsafe_allow_html=True)

    # ---------------- Tab-like selection ----------------
    dataset_source = st.radio(
        "Dataset Source",
        options=["📁 Existing Project Dataset", "⬆️ Upload New Dataset"],
        index=0,
        label_visibility="collapsed",
        help="Select an existing dataset from the project folder or upload a new one from your computer.",
    )

    use_existing = dataset_source.startswith("📁")

    # ================================================================
    # WORKFLOW A: Existing Project Dataset (UNCHANGED BEHAVIOR)
    # ================================================================
    if use_existing:
        registry = DatasetRegistry()
        available_datasets = registry.list_datasets()

        if not available_datasets:
            st.warning("No datasets found in the data/ folder.")
        else:
            selected = st.selectbox(
                "Select dataset",
                options=available_datasets,
                index=0,
                label_visibility="collapsed",
            )
            load_btn = st.button("Load Dataset", use_container_width=True)
            auto_load = st.session_state.df is None and not st.session_state.get("upload_history")

            if load_btn or auto_load:
                with st.status("Loading dataset...", expanded=False) as status:
                    status.update(label="Reading file...")
                    result = registry.load(selected)
                    success, data = result

                    if not success:
                        status.update(label="Failed", state="error")
                        st.error(data)
                    else:
                        status.update(label="Cleaning data...")
                        df, _ = DataCleaner().clean(data)
                        status.update(label="Profiling...")
                        profile = DataProfiler().profile(df)
                        status.update(label="Building business knowledge...")
                        schema = BusinessKnowledgeBuilder().build(profile, selected)
                        status.update(label="Computing KPIs...")
                        kpis = compute_kpis(df, schema)

                        st.session_state.df = df
                        st.session_state.profile = profile
                        st.session_state.session = SessionManager()
                        st.session_state.context = ConversationContext()
                        st.session_state.business_schema = schema
                        st.session_state.loaded_dataset = selected
                        st.session_state.kpis = kpis

                        status.update(label=f"✅ Loaded: {selected}", state="complete")
                        st.rerun()

    # ================================================================
    # WORKFLOW B: Upload New Dataset (ALL 10 FEATURES)
    # ================================================================
    else:
        # ✅ Feature 2: Professional Drag & Drop Upload Area
        uploaded_file = render_upload_area()

        if uploaded_file is not None:
            manager = UploadManager()

            # ✅ Feature 9: Error Handling — validate first
            ok, error, preview = manager.validate_file(uploaded_file)

            if not ok:
                st.error(f"❌ {error}")
            else:
                # ✅ Feature 4: File Preview Before Processing
                render_file_preview(preview)
                st.session_state.upload_preview = preview

                # ✅ Feature 1: Excel Sheet Selector
                sheet_name = None
                if preview.extension in ("XLSX", "XLS"):
                    excel_info = get_excel_info(uploaded_file)
                    if excel_info.password_protected:
                        st.error("❌ Password-protected Excel. Please remove the password and retry.")
                        st.stop()
                    if excel_info.error:
                        st.error(f"❌ {excel_info.error}")
                        st.stop()

                    # Only show selector if multiple sheets
                    if len(excel_info.sheet_names) > 1:
                        sheet_name = render_sheet_selector(excel_info)
                    else:
                        sheet_name = excel_info.selected_sheet

                    st.session_state.upload_excel_info = excel_info

                # ✅ Feature 6: Automatic Header Row Detection
                ok_raw, df_raw, error_raw = manager.load_raw(
                    uploaded_file, header_row=0, sheet_name=sheet_name
                )
                if not ok_raw:
                    st.error(f"❌ {error_raw}")
                else:
                    detected_header = manager.detect_header(df_raw)

                    # Allow manual override
                    header_row = render_header_selector(detected_header)
                    st.session_state.upload_header_row = header_row

                    # Load with chosen header for type detection
                    ok_load, df_loaded, error_load = manager.load_raw(
                        uploaded_file, header_row=header_row, sheet_name=sheet_name
                    )
                    if not ok_load:
                        st.error(f"❌ {error_load}")
                    else:
                        # Quick profile to show detected types
                        quick_profile = DataProfiler().profile(df_loaded)

                        # ✅ Feature 5: Column Type Override
                        overrides = render_type_override(quick_profile)
                        st.session_state.upload_overrides = overrides

                        # ✅ Feature 8: Progress Feedback via st.status
                        if st.button("🚀 Process Dataset", use_container_width=True, key="process_upload"):
                            with st.status("Processing dataset...", expanded=True) as status:
                                try:
                                    # Apply overrides
                                    if overrides:
                                        status.update(label="Detecting column types...")
                                        df_loaded, type_errors = manager.apply_overrides(df_loaded, overrides)
                                        if type_errors:
                                            for err in type_errors:
                                                st.warning(f"⚠️ {err}")

                                    status.update(label="Cleaning dataset...")
                                    df_clean, clean_report = DataCleaner().clean(df_loaded)

                                    status.update(label="Profiling dataset...")
                                    profile = DataProfiler().profile(df_clean)

                                    status.update(label="Generating business knowledge...")
                                    schema = BusinessKnowledgeBuilder().build(profile, preview.filename)

                                    status.update(label="Preparing KPIs...")
                                    kpis = compute_kpis(df_clean, schema)

                                    status.update(label="Ready ✓", state="complete")

                                    # ✅ Feature 7: Upload Pipeline — store in session state
                                    st.session_state.df = df_clean
                                    st.session_state.profile = profile
                                    st.session_state.session = SessionManager()
                                    st.session_state.context = ConversationContext()
                                    st.session_state.business_schema = schema
                                    st.session_state.loaded_dataset = preview.filename
                                    st.session_state.kpis = kpis

                                    # ✅ Feature 3: Upload History Cache
                                    st.session_state.upload_history[preview.filename] = {
                                        "df": df_clean,
                                        "profile": profile,
                                        "schema": schema,
                                        "kpis": kpis,
                                        "metadata": {
                                            "filename": preview.filename,
                                            "size_bytes": preview.size_bytes,
                                            "extension": preview.extension,
                                            "sheet_name": sheet_name,
                                            "header_row": header_row,
                                            "overrides": overrides,
                                            "clean_report": clean_report,
                                        },
                                    }

                                    st.success(f"✅ **{preview.filename}** loaded successfully!")
                                    st.rerun()

                                except Exception as e:
                                    status.update(label="Error", state="error")
                                    st.error(f"Processing failed: {e}")

        # ✅ Feature 3: Upload History Dropdown
        if st.session_state.get("upload_history"):
            selected_history = render_upload_history(st.session_state.upload_history)
            if selected_history and st.button("↻ Switch to Selected", use_container_width=True, key="switch_history"):
                entry = st.session_state.upload_history[selected_history]
                st.session_state.df = entry["df"]
                st.session_state.profile = entry["profile"]
                st.session_state.session = SessionManager()
                st.session_state.context = ConversationContext()
                st.session_state.business_schema = entry["schema"]
                st.session_state.loaded_dataset = selected_history
                st.session_state.kpis = entry["kpis"]
                st.rerun()

        # Show supported formats hint
        st.caption(
            "Supported: **CSV**, **Excel (.xlsx)**, **Excel (.xls)** | "
            "Max: **50 MB**"
        )

    st.divider()

    # ================================================================
    # DATASET INFO PANEL (shared by both workflows)
    # ================================================================
    if st.session_state.df is not None:
        p = st.session_state.profile

        if USE_NEW_UI:
            render_section_label("Dataset Info")
            render_sidebar_metric("File", st.session_state.loaded_dataset)
            render_sidebar_metric("Rows", f"{p.rows:,}")
            render_sidebar_metric("Columns", str(p.columns))
        else:
            st.markdown('<div class="section-label">Dataset Info</div>', unsafe_allow_html=True)
            st.markdown(f"""
                <div class="sidebar-metric">
                    <span class="sidebar-metric-label">File</span>
                    <span class="sidebar-metric-value">{st.session_state.loaded_dataset}</span>
                </div>
                <div class="sidebar-metric">
                    <span class="sidebar-metric-label">Rows</span>
                    <span class="sidebar-metric-value">{p.rows:,}</span>
                </div>
                <div class="sidebar-metric">
                    <span class="sidebar-metric-label">Columns</span>
                    <span class="sidebar-metric-value">{p.columns}</span>
                </div>
            """, unsafe_allow_html=True)

        schema = st.session_state.business_schema
        if schema:
            st.divider()

            if USE_NEW_UI:
                render_section_label("Key Metrics")
            else:
                st.markdown('<div class="section-label">Key Metrics</div>', unsafe_allow_html=True)

            for kpi in schema.kpi_columns[:4]:
                st.markdown(
                    f"<div style='padding:0.25rem 0;font-size:0.78rem;"
                    f"color:#D1FAE5;'>▸ {kpi}</div>",
                    unsafe_allow_html=True
                )

            if USE_NEW_UI:
                render_section_label("Dimensions", margin_top="0.75rem")
            else:
                st.markdown('<div class="section-label" style="margin-top:1rem;">Dimensions</div>', unsafe_allow_html=True)

            for dim in schema.dimensions[:5]:
                st.markdown(
                    f"<div style='padding:0.2rem 0;font-size:0.73rem;"
                    f"color:#9CA3AF;'>• {dim}</div>",
                    unsafe_allow_html=True
                )

    st.divider()
    if st.button("Clear Chat", use_container_width=True):
        st.session_state.session.clear()
        st.session_state.context.clear()
        st.rerun()

# ------------------------------------------------------------------
# Header
# ------------------------------------------------------------------

dataset_name = st.session_state.loaded_dataset or "No dataset loaded"

if USE_NEW_UI:
    render_app_header(dataset_name)
else:
    st.markdown(f"""
        <div style="display:flex;align-items:center;justify-content:space-between;
                    padding-bottom:1rem;border-bottom:1px solid #E5E7EB;
                    margin-bottom:1.5rem;">
            <div>
                <h2 style="margin:0;color:#111827;font-size:1.4rem;font-weight:700;">
                    AI BI Assistant
                </h2>
                <span style="font-size:0.8rem;color:#6B7280;">{dataset_name}</span>
            </div>
            <span class="status-badge">● Connected</span>
        </div>
    """, unsafe_allow_html=True)

if st.session_state.df is None:
    if USE_NEW_UI:
        render_empty_state()
    else:
        st.markdown("""
            <div style="text-align:center;padding:4rem 2rem;color:#6B7280;">
                <div style="font-size:2rem;margin-bottom:1rem;">⬡</div>
                <div style="font-size:1.1rem;font-weight:600;color:#111827;
                            margin-bottom:0.5rem;">No dataset loaded</div>
                <div style="font-size:0.9rem;">Select a dataset from the sidebar or upload a new one</div>
            </div>
        """, unsafe_allow_html=True)
    st.stop()

# ------------------------------------------------------------------
# KPI Dashboard
# ------------------------------------------------------------------

kpis = st.session_state.kpis
if kpis:
    kpi_icons = {
        "Total Sales": ("💰", "#2563EB"),
        "Total Profit": ("📈", "#16A34A"),
        "Orders": ("📦", "#7C3AED"),
        "Customers": ("👥", "#0891B2"),
        "Top Region": ("🌍", "#D97706"),
        "Top Category": ("🏷️", "#DC2626"),
        "Records": ("📋", "#2563EB"),
        "Unique Names": ("👤", "#0891B2"),
    }
    items = list(kpis.items())
    cols = st.columns(min(len(items), 4))
    for i, (label, value) in enumerate(items[:4]):
        icon, color = kpi_icons.get(label, ("📊", "#2563EB"))
        with cols[i]:
            if USE_NEW_UI:
                render_kpi_card(label, value, icon, color)
            else:
                st.metric(label=label, value=value)

    if len(items) > 4:
        cols2 = st.columns(len(items) - 4)
        for i, (label, value) in enumerate(items[4:]):
            icon, color = kpi_icons.get(label, ("📊", "#2563EB"))
            with cols2[i]:
                if USE_NEW_UI:
                    render_kpi_card(label, value, icon, color)
                else:
                    st.metric(label=label, value=value)

    st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

# ------------------------------------------------------------------
# Chat history
# ------------------------------------------------------------------

def render_entry(entry: ChatEntry, index: int):
    with st.chat_message("user"):
        st.write(entry.question)
    with st.chat_message("assistant"):
        if entry.error:
            if USE_NEW_UI:
                render_planning_error(entry.error)
            else:
                st.error(entry.error)
            return
        if entry.figure:
            st.plotly_chart(entry.figure, use_container_width=True)
        if entry.data:
            with st.expander("View Data Table"):
                st.dataframe(pd.DataFrame(entry.data), use_container_width=True)
        if entry.explanation:
            if USE_NEW_UI:
                render_insight_card(entry.explanation)
            else:
                st.markdown(entry.explanation)
        if entry.is_time_series:
            if entry.forecast_figure:
                st.plotly_chart(entry.forecast_figure, use_container_width=True)
                if entry.forecast_info:
                    st.caption(
                        f"ML Model: Linear Regression | "
                        f"Trend: {entry.forecast_info['trend']} | "
                        f"Monthly change: ${entry.forecast_info['slope']:,.2f}"
                    )
            else:
                if st.button("📈 Show 3-Month Forecast", key=f"fc_{index}"):
                    result_df = pd.DataFrame(entry.data)
                    date_col = result_df.columns[0]
                    metric_col = result_df.columns[1]
                    fe = ForecastEngine()
                    try:
                        forecast_df = fe.forecast(result_df, date_col, metric_col)
                        model_info = fe.get_model_info(result_df, date_col, metric_col)
                        hist = forecast_df[forecast_df["type"] == "historical"]
                        fcast = forecast_df[forecast_df["type"] == "forecast"]
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=hist[date_col], y=hist[metric_col],
                            mode="lines+markers", name="Historical",
                            line=dict(color="#2563EB", width=2)
                        ))
                        fig.add_trace(go.Scatter(
                            x=fcast[date_col], y=fcast[metric_col],
                            mode="lines+markers", name="Forecast",
                            line=dict(color="#F97316", dash="dash", width=2)
                        ))
                        fig.update_layout(
                            title="Sales Forecast — Next 3 Months (Linear Regression)",
                            template="plotly_white",
                            height=380,
                            margin=dict(l=20, r=20, t=40, b=20),
                            paper_bgcolor="white",
                            plot_bgcolor="white",
                        )
                        entry.forecast_figure = fig
                        entry.forecast_info = model_info
                        st.rerun()
                    except Exception as e:
                        st.error(f"Forecast failed: {e}")


for i, entry in enumerate(st.session_state.session.get_history()):
    render_entry(entry, i)

# ------------------------------------------------------------------
# Chat input
# ------------------------------------------------------------------

question = st.chat_input("Ask a business question about your data...")

if question:
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        status = st.status("Processing...")
        try:
            profile = st.session_state.profile
            df = st.session_state.df
            context = st.session_state.context
            business_schema = st.session_state.business_schema

            status.update(label="Creating execution plan...")
            sp, up = PromptBuilder().build(
                profile, question,
                context_summary=context.get_context_summary(),
                business_schema=business_schema,
            )
            raw = AIClient().ask(sp, up)

            status.update(label="Validating plan...")
            ok, plan_or_error = CommandValidator().validate(
                raw, profile, original_question=question
            )
            if not ok:
                status.update(label="Done", state="error")
                entry = ChatEntry(question=question, error=plan_or_error)
                st.session_state.session.add(entry)
                if USE_NEW_UI:
                    render_planning_error(plan_or_error)
                else:
                    st.error(plan_or_error)
                st.stop()

            status.update(label="Running analysis...")
            result = AnalysisEngine().execute(df, plan_or_error, question)
            if not result.success:
                status.update(label="Done", state="error")
                entry = ChatEntry(question=question, error=result.error)
                st.session_state.session.add(entry)
                if USE_NEW_UI:
                    render_planning_error(result.error)
                else:
                    st.error(result.error)
                st.stop()

            status.update(label="Building visualisation...")
            figure = ChartEngine().render(result, plan_or_error.visualization)
            if figure:
                st.plotly_chart(figure, use_container_width=True)

            with st.expander("View Data Table"):
                st.dataframe(pd.DataFrame(result.data), use_container_width=True)

            status.update(label="Generating insight...")
            explanation = ExplanationEngine().explain(result)
            if USE_NEW_UI:
                render_insight_card(explanation)
            else:
                st.markdown(explanation)

            status.update(label="Done ✓", state="complete")

            is_time_series = any(
                s.operation == "time_series" for s in plan_or_error.steps
            )

            entry = ChatEntry(
                question=question, explanation=explanation,
                data=result.data, figure=figure,
                is_time_series=is_time_series,
            )
            st.session_state.session.add(entry)
            context.add_turn(question, plan_or_error, result.data)

            if is_time_series:
                st.info("Click '📈 Show 3-Month Forecast' above to run ML forecasting.")

        except Exception as e:
            status.update(label="Error", state="error")
            if USE_NEW_UI:
                render_planning_error(f"An unexpected error occurred. Please try again.\n\nDetail: {e}")
            else:
                st.error(f"An unexpected error occurred. Please try again.\n\nDetail: {e}")