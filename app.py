import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="AI BI Assistant",
    page_icon="⬡",
    layout="wide",
)

from ui.styles import inject_styles
inject_styles()

from core.business_knowledge import BusinessKnowledgeBuilder
from core.conversation_context import ConversationContext
from core.data_cleaner import DataCleaner
from core.data_profiler import DataProfiler
from core.prompt_builder import PromptBuilder
from core.ai_client import AIClient
from core.command_validator import CommandValidator
from core.analysis_engine import AnalysisEngine
from core.chart_engine import ChartEngine
from core.explanation_engine import ExplanationEngine
from core.session_manager import SessionManager, ChatEntry
from core.forecast_engine import ForecastEngine
from core.dataset_registry import DatasetRegistry

# ------------------------------------------------------------------
# Session state
# ------------------------------------------------------------------

if "df" not in st.session_state:
    st.session_state.df = None
if "profile" not in st.session_state:
    st.session_state.profile = None
if "session" not in st.session_state:
    st.session_state.session = SessionManager()
if "context" not in st.session_state:
    st.session_state.context = ConversationContext()
if "business_schema" not in st.session_state:
    st.session_state.business_schema = None
if "loaded_dataset" not in st.session_state:
    st.session_state.loaded_dataset = None

# ------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------

with st.sidebar:
    st.markdown("""
        <div class="sidebar-logo">
            <div class="sidebar-logo-text">⬡ AI BI Assistant</div>
            <div class="sidebar-logo-sub">Enterprise Intelligence Platform</div>
        </div>
    """, unsafe_allow_html=True)

    registry = DatasetRegistry()
    available_datasets = registry.list_datasets()

    st.markdown('<div class="section-label">Dataset</div>', unsafe_allow_html=True)

    if not available_datasets:
        st.warning("No datasets found in data/ folder.")
    else:
        selected = st.selectbox(
            "Select Dataset",
            options=available_datasets,
            index=0,
            label_visibility="collapsed",
        )

        load_btn = st.button("Load Dataset", use_container_width=True)

        auto_load = st.session_state.df is None
        if load_btn or auto_load:
            with st.spinner("Loading dataset..."):
                result = registry.load(selected)
                success, data = result
                if not success:
                    st.error(data)
                else:
                    df, _ = DataCleaner().clean(data)
                    profile = DataProfiler().profile(df)
                    business_schema = BusinessKnowledgeBuilder().build(
                        profile, selected
                    )
                    st.session_state.df = df
                    st.session_state.profile = profile
                    st.session_state.session = SessionManager()
                    st.session_state.context = ConversationContext()
                    st.session_state.business_schema = business_schema
                    st.session_state.loaded_dataset = selected

    st.divider()

    if st.session_state.df is not None:
        profile = st.session_state.profile
        schema = st.session_state.business_schema

        st.markdown(
            '<div class="section-label">Dataset Info</div>',
            unsafe_allow_html=True
        )
        st.markdown(f"""
            <div class="sidebar-metric">
                <span class="sidebar-metric-label">File</span>
                <span class="sidebar-metric-value">{st.session_state.loaded_dataset}</span>
            </div>
            <div class="sidebar-metric">
                <span class="sidebar-metric-label">Rows</span>
                <span class="sidebar-metric-value">{profile.rows:,}</span>
            </div>
            <div class="sidebar-metric">
                <span class="sidebar-metric-label">Columns</span>
                <span class="sidebar-metric-value">{profile.columns}</span>
            </div>
        """, unsafe_allow_html=True)

        if schema:
            st.divider()
            st.markdown(
                '<div class="section-label">Key Metrics</div>',
                unsafe_allow_html=True
            )
            for kpi in schema.kpi_columns[:4]:
                st.markdown(
                    f"<div style='padding:0.3rem 0;font-size:0.8rem;"
                    f"color:#D1FAE5;'>▸ {kpi}</div>",
                    unsafe_allow_html=True
                )

            st.markdown(
                '<div class="section-label" style="margin-top:1rem;">'
                'Dimensions</div>',
                unsafe_allow_html=True
            )
            for dim in schema.dimensions[:5]:
                st.markdown(
                    f"<div style='padding:0.2rem 0;font-size:0.75rem;"
                    f"color:#9CA3AF;'>• {dim}</div>",
                    unsafe_allow_html=True
                )

    st.divider()

    if st.button("Clear Chat", use_container_width=True):
        if st.session_state.session:
            st.session_state.session.clear()
        if st.session_state.context:
            st.session_state.context.clear()
        st.rerun()

# ------------------------------------------------------------------
# Main header
# ------------------------------------------------------------------

dataset_name = st.session_state.loaded_dataset or "No dataset loaded"
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
    st.markdown("""
        <div style="text-align:center;padding:4rem 2rem;color:#6B7280;">
            <div style="font-size:2rem;margin-bottom:1rem;">⬡</div>
            <div style="font-size:1.1rem;font-weight:600;color:#111827;
                        margin-bottom:0.5rem;">
                No dataset loaded
            </div>
            <div style="font-size:0.9rem;">
                Select a dataset from the sidebar and click Load Dataset
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

# ------------------------------------------------------------------
# Professional error renderer
# ------------------------------------------------------------------

def render_planning_error(message: str):
    """Render a professional narrowing/error message instead of raw error."""
    st.markdown(f"""
        <div style="background:#FFF7ED;border:1px solid #FED7AA;border-left:4px solid
                    #F97316;border-radius:8px;padding:1rem 1.25rem;margin:0.5rem 0;">
            <div style="font-weight:600;color:#9A3412;margin-bottom:0.5rem;
                        font-size:0.9rem;">
                ⚠ Unable to process this request
            </div>
            <div style="color:#7C2D12;font-size:0.85rem;white-space:pre-line;">
                {message}
            </div>
        </div>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------
# Chat history renderer
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
                st.dataframe(
                    pd.DataFrame(entry.data),
                    use_container_width=True
                )
        if entry.explanation:
            st.markdown(entry.explanation)
        if entry.is_time_series:
            if entry.forecast_figure:
                st.plotly_chart(
                    entry.forecast_figure,
                    use_container_width=True
                )
                if entry.forecast_info:
                    st.caption(
                        f"ML Model: Linear Regression | "
                        f"Trend: {entry.forecast_info['trend']} | "
                        f"Monthly change: "
                        f"${entry.forecast_info['slope']:,.2f}"
                    )
            else:
                if st.button(
                    "📈 Show 3-Month Forecast",
                    key=f"fc_{index}"
                ):
                    result_df = pd.DataFrame(entry.data)
                    date_col = result_df.columns[0]
                    metric_col = result_df.columns[1]
                    fe = ForecastEngine()
                    forecast_df = fe.forecast(result_df, date_col, metric_col)
                    model_info = fe.get_model_info(
                        result_df, date_col, metric_col
                    )
                    hist = forecast_df[forecast_df["type"] == "historical"]
                    fcast = forecast_df[forecast_df["type"] == "forecast"]
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=hist[date_col], y=hist[metric_col],
                        mode="lines+markers", name="Historical",
                        line=dict(color="#60a5fa")
                    ))
                    fig.add_trace(go.Scatter(
                        x=fcast[date_col], y=fcast[metric_col],
                        mode="lines+markers", name="Forecast",
                        line=dict(color="#f97316", dash="dash")
                    ))
                    fig.update_layout(
                        title="Sales Forecast — Next 3 Months"
                               " (Linear Regression)",
                        template="plotly_dark",
                        height=400,
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
        status = st.status("Analysing...", expanded=False)

        try:
            profile = st.session_state.profile
            df = st.session_state.df
            context = st.session_state.context
            business_schema = st.session_state.business_schema

            status.update(label="Building execution plan...")
            sp, up = PromptBuilder().build(
                profile,
                question,
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

            status.update(label="Executing analysis...")
            result = AnalysisEngine().execute(df, plan_or_error, question)

            if not result.success:
                status.update(label="Done", state="error", expanded=False)
                entry = ChatEntry(question=question, error=result.error)
                st.session_state.session.add(entry)
                render_planning_error(result.error)
                st.stop()

            status.update(label="Rendering visualisation...")
            figure = ChartEngine().render(result, plan_or_error.visualization)
            if figure:
                st.plotly_chart(figure, use_container_width=True)

            with st.expander("View Data Table"):
                st.dataframe(
                    pd.DataFrame(result.data),
                    use_container_width=True
                )

            status.update(label="Generating insights...")
            explanation = ExplanationEngine().explain(result)
            st.markdown(explanation)

            status.update(label="Done", state="complete", expanded=False)

            is_time_series = any(
                s.operation == "time_series"
                for s in plan_or_error.steps
            )

            entry = ChatEntry(
                question=question,
                explanation=explanation,
                data=result.data,
                figure=figure,
                is_time_series=is_time_series,
            )
            st.session_state.session.add(entry)
            context.add_turn(question, plan_or_error, result.data)

            if is_time_series:
                st.info(
                    "Scroll up and click "
                    "'📈 Show 3-Month Forecast' to run ML forecasting."
                )

        except Exception as e:
            status.update(label="Error", state="error", expanded=False)
            render_planning_error(
                f"An unexpected error occurred. Please try again.\n\n"
                f"Technical detail: {e}"
            )