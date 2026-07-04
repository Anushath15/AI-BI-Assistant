"""
app.py

Main Streamlit application.
Wires all backend modules into a chat interface.

Pipeline per question:
1. PromptBuilder  — builds prompt with schema + context + business knowledge
2. AIClient       — returns ExecutionPlan JSON
3. CommandValidator — validates against real dataset
4. AnalysisEngine — executes plan
5. ChartEngine    — renders chart
6. ExplanationEngine — generates business explanation
7. ConversationContext — stores turn for follow-up questions
"""

import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from dotenv import load_dotenv

from core.business_knowledge import BusinessKnowledgeBuilder
from core.conversation_context import ConversationContext
from core.data_loader import load_csv
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

load_dotenv()

st.set_page_config(
    page_title="AI BI Assistant",
    page_icon="📊",
    layout="wide",
)

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
    st.title("📊 AI BI Assistant")
    st.markdown("Ask business questions about your company data.")
    st.divider()

    # Dataset selector — enterprise mode
    from core.dataset_registry import DatasetRegistry
    registry = DatasetRegistry()
    available_datasets = registry.list_datasets()

    if not available_datasets:
        st.warning("No datasets found in data/ folder.")
    else:
        selected = st.selectbox(
            "Select Dataset",
            options=available_datasets,
            index=0,
        )

        load_btn = st.button("Load Dataset")
        auto_load = st.session_state.df is None
        if load_btn or auto_load:
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

                st.success(
                    f"Loaded {profile.rows:,} rows × {profile.columns} columns"
                )

    st.divider()

    if st.session_state.business_schema:
        st.markdown("**Key Metrics**")
        for kpi in st.session_state.business_schema.kpi_columns[:5]:
            st.caption(f"📊 {kpi}")

        st.markdown("**Dimensions**")
        for dim in st.session_state.business_schema.dimensions[:5]:
            st.caption(f"• {dim}")

    st.divider()

    if st.button("Clear Chat"):
        st.session_state.session.clear()
        st.session_state.context.clear()
        st.rerun()

# ------------------------------------------------------------------
# Main area
# ------------------------------------------------------------------

st.title("📊 AI BI Assistant")
st.caption("Ask any business question about your data.")

if st.session_state.df is None:
    st.info("Upload a CSV file from the sidebar to get started.")
    st.stop()


# ------------------------------------------------------------------
# Chat history renderer
# ------------------------------------------------------------------

def render_entry(entry: ChatEntry, index: int):
    with st.chat_message("user"):
        st.write(entry.question)
    with st.chat_message("assistant"):
        if entry.error:
            st.error(entry.error)
            return
        if entry.figure:
            st.plotly_chart(entry.figure, use_container_width=True)
        if entry.data:
            with st.expander("View Data Table"):
                st.dataframe(pd.DataFrame(entry.data), use_container_width=True)
        if entry.explanation:
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
                    forecast_df = fe.forecast(result_df, date_col, metric_col)
                    model_info = fe.get_model_info(result_df, date_col, metric_col)
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
                        title="Sales Forecast — Next 3 Months (Linear Regression)",
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

question = st.chat_input("Ask a question about your data...")

if question:
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant"):
        with st.spinner("Analysing..."):
            try:
                profile = st.session_state.profile
                df = st.session_state.df
                context = st.session_state.context
                business_schema = st.session_state.business_schema

                sp, up = PromptBuilder().build(
                    profile,
                    question,
                    context_summary=context.get_context_summary(),
                    business_schema=business_schema,
                )
                raw = AIClient().ask(sp, up)

                ok, plan_or_error = CommandValidator().validate(raw, profile)
                if not ok:
                    entry = ChatEntry(
                        question=question,
                        error=f"Planning error: {plan_or_error}"
                    )
                    st.session_state.session.add(entry)
                    st.error(entry.error)
                    st.stop()

                result = AnalysisEngine().execute(df, plan_or_error, question)
                if not result.success:
                    entry = ChatEntry(question=question, error=result.error)
                    st.session_state.session.add(entry)
                    st.error(entry.error)
                    st.stop()

                figure = ChartEngine().render(result, plan_or_error.visualization)
                if figure:
                    st.plotly_chart(figure, use_container_width=True)

                with st.expander("View Data Table"):
                    st.dataframe(
                        pd.DataFrame(result.data),
                        use_container_width=True
                    )

                explanation = ExplanationEngine().explain(result)
                st.markdown(explanation)

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
                    st.info("Scroll up and click '📈 Show 3-Month Forecast' to run ML forecasting.")

            except Exception as e:
                st.error(f"Unexpected error: {e}")