import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dotenv import load_dotenv

# ---------------------------
# Load Environment Variables
# ---------------------------
load_dotenv()

# ---------------------------
# Streamlit Configuration
# ---------------------------
st.set_page_config(
    page_title="AI BI Assistant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------
# UI
# ---------------------------
from ui.styles import apply_global_styles

from ui.components import (
    render_app_header,
    render_empty_state,
    render_insight_card,
    render_kpi_card,
    render_planning_error,
    render_section_label,
    render_sidebar_metric,
)
# Apply global theme
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
# ------------------------------------------------------------------
# Session state
# ------------------------------------------------------------------

for key, default in {
    "df": None, "profile": None,
    "session": None, "context": None,
    "business_schema": None, "loaded_dataset": None,
    "kpis": {},
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

if st.session_state.session is None:
    st.session_state.session = SessionManager()
if st.session_state.context is None:
    st.session_state.context = ConversationContext()

# ------------------------------------------------------------------
# KPI computation
# ------------------------------------------------------------------

def compute_kpis(df: pd.DataFrame, schema) -> dict:
    kpis = {}
    try:
        if "Sales" in df.columns:
            kpis["Total Sales"] = f"${df['Sales'].sum():,.0f}"
        if "Profit" in df.columns:
            kpis["Total Profit"] = f"${df['Profit'].sum():,.0f}"
        if "Order ID" in df.columns:
            kpis["Orders"] = f"{df['Order ID'].nunique():,}"
        if "Customer Name" in df.columns:
            kpis["Customers"] = f"{df['Customer Name'].nunique():,}"
        if "Region" in df.columns and "Sales" in df.columns:
            top = df.groupby("Region")["Sales"].sum().idxmax()
            kpis["Top Region"] = top
        if "Category" in df.columns and "Sales" in df.columns:
            top = df.groupby("Category")["Sales"].sum().idxmax()
            kpis["Top Category"] = top
    except Exception:
        pass
    return kpis

# ------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------

with st.sidebar:
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

    registry = DatasetRegistry()
    available_datasets = registry.list_datasets()

    render_section_label("Dataset")

    if not available_datasets:
        st.warning("No datasets in data/ folder.")
    else:
        selected = st.selectbox(
            "dataset", options=available_datasets,
            index=0, label_visibility="collapsed",
        )
        load_btn = st.button("Load Dataset", use_container_width=True)
        auto_load = st.session_state.df is None

        if load_btn or auto_load:
            with st.spinner("Loading..."):
                result = registry.load(selected)
                success, data = result
                if not success:
                    st.error(data)
                else:
                    df, _ = DataCleaner().clean(data)
                    profile = DataProfiler().profile(df)
                    schema = BusinessKnowledgeBuilder().build(profile, selected)
                    st.session_state.df = df
                    st.session_state.profile = profile
                    st.session_state.session = SessionManager()
                    st.session_state.context = ConversationContext()
                    st.session_state.business_schema = schema
                    st.session_state.loaded_dataset = selected
                    st.session_state.kpis = compute_kpis(df, schema)

    st.divider()

    if st.session_state.df is not None:
        p = st.session_state.profile
        render_section_label("Dataset Info")
        render_sidebar_metric("File", st.session_state.loaded_dataset)
        render_sidebar_metric("Rows", f"{p.rows:,}")
        render_sidebar_metric("Columns", str(p.columns))

        schema = st.session_state.business_schema
        if schema:
            st.divider()
            render_section_label("Key Metrics")
            for kpi in schema.kpi_columns[:4]:
                st.markdown(
                    f"<div style='padding:0.25rem 0;font-size:0.78rem;"
                    f"color:#D1FAE5;'>▸ {kpi}</div>",
                    unsafe_allow_html=True
                )
            render_section_label("Dimensions", margin_top="0.75rem")
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
render_app_header(dataset_name)

if st.session_state.df is None:
    render_empty_state()
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
    }
    items = list(kpis.items())
    cols = st.columns(min(len(items), 4))
    for i, (label, value) in enumerate(items[:4]):
        icon, color = kpi_icons.get(label, ("📊", "#2563EB"))
        with cols[i]:
            render_kpi_card(label, value, icon, color)

    if len(items) > 4:
        cols2 = st.columns(len(items) - 4)
        for i, (label, value) in enumerate(items[4:]):
            icon, color = kpi_icons.get(label, ("📊", "#2563EB"))
            with cols2[i]:
                render_kpi_card(label, value, icon, color)

    st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

# ------------------------------------------------------------------
# Chat history
# ------------------------------------------------------------------

def render_entry(entry: ChatEntry, index: int):
    with st.chat_message("user"):
        st.write(entry.question)
    with st.chat_message("assistant"):
        if entry.error:
            render_planning_error(entry.error)
            return
        if entry.figure:
            st.plotly_chart(entry.figure, use_container_width=True)
        if entry.data:
            with st.expander("View Data Table"):
                st.dataframe(pd.DataFrame(entry.data), use_container_width=True)
        if entry.explanation:
            render_insight_card(entry.explanation)
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
        status = st.status("Processing...", expanded=False)
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
                status.update(label="Done", state="error", expanded=False)
                entry = ChatEntry(question=question, error=plan_or_error)
                st.session_state.session.add(entry)
                render_planning_error(plan_or_error)
                st.stop()

            status.update(label="Running analysis...")
            result = AnalysisEngine().execute(df, plan_or_error, question)
            if not result.success:
                status.update(label="Done", state="error", expanded=False)
                entry = ChatEntry(question=question, error=result.error)
                st.session_state.session.add(entry)
                render_planning_error(result.error)
                st.stop()

            status.update(label="Building visualisation...")
            figure = ChartEngine().render(result, plan_or_error.visualization)
            if figure:
                # Switch to white plotly theme for consistency
                figure.update_layout(
                    template="plotly_white",
                    paper_bgcolor="white",
                    plot_bgcolor="white",
                    margin=dict(l=20, r=20, t=40, b=20),
                    height=380,
                )
                st.plotly_chart(figure, use_container_width=True)

            with st.expander("View Data Table"):
                st.dataframe(pd.DataFrame(result.data), use_container_width=True)

            status.update(label="Generating insight...")
            explanation = ExplanationEngine().explain(result)
            render_insight_card(explanation)

            status.update(label="Done ✓", state="complete", expanded=False)

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
            status.update(label="Error", state="error", expanded=False)
            render_planning_error(f"An unexpected error occurred. Please try again.\n\nDetail: {e}")