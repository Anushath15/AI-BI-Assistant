import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

from core.data_loader import load_csv
from core.data_cleaner import DataCleaner
from core.data_profiler import DataProfiler
from core.prompt_builder import PromptBuilder
from core.ai_client import AIClient
from core.command_validator import CommandValidator
from core.analysis_engine import AnalysisEngine
from core.chart_engine import ChartEngine
from core.explanation_engine import ExplanationEngine

load_dotenv()

# ------------------------------------------------------------------
# Page config
# ------------------------------------------------------------------

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
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ------------------------------------------------------------------
# Sidebar — upload
# ------------------------------------------------------------------

with st.sidebar:
    st.title("📊 AI BI Assistant")
    st.markdown("Upload a CSV and ask questions in plain English.")
    st.divider()

    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

    if uploaded_file:
        success, result = load_csv(uploaded_file)

        if not success:
            st.error(result)
        else:
            df, report = DataCleaner().clean(result)
            profile = DataProfiler().profile(df)

            st.session_state.df = df
            st.session_state.profile = profile

            st.success(f"Loaded {profile.rows:,} rows × {profile.columns} columns")
            st.divider()

            st.markdown("**Columns**")
            for col in profile.column_names:
                st.caption(f"• {col}")

            if st.button("Clear Chat"):
                st.session_state.chat_history = []
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
# Chat history display
# ------------------------------------------------------------------

for entry in st.session_state.chat_history:
    with st.chat_message("user"):
        st.write(entry["question"])

    with st.chat_message("assistant"):
        if entry.get("error"):
            st.error(entry["error"])
        else:
            if entry.get("figure"):
                st.plotly_chart(entry["figure"], use_container_width=True)
            if entry.get("data"):
                with st.expander("View Data Table"):
                    st.dataframe(
                        pd.DataFrame(entry["data"]),
                        use_container_width=True,
                    )
            if entry.get("explanation"):
                st.markdown(entry["explanation"])

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

                # Step 1: Build prompt and get execution plan
                sp, up = PromptBuilder().build(profile, question)
                raw = AIClient().ask(sp, up)

                # Step 2: Validate plan
                ok, plan_or_error = CommandValidator().validate(raw, profile)
                if not ok:
                    st.error(f"Planning error: {plan_or_error}")
                    st.session_state.chat_history.append({
                        "question": question,
                        "error": f"Planning error: {plan_or_error}",
                    })
                    st.stop()

                # Step 3: Execute plan
                result = AnalysisEngine().execute(df, plan_or_error, question)
                if not result.success:
                    st.error(result.error)
                    st.session_state.chat_history.append({
                        "question": question,
                        "error": result.error,
                    })
                    st.stop()

                # Step 4: Render chart
                figure = ChartEngine().render(result, plan_or_error.visualization)
                if figure:
                    st.plotly_chart(figure, use_container_width=True)

                # Step 5: Show data table
                with st.expander("View Data Table"):
                    st.dataframe(
                        pd.DataFrame(result.data),
                        use_container_width=True,
                    )

                # Step 6: Generate explanation
                explanation = ExplanationEngine().explain(result)
                st.markdown(explanation)

                # Save to chat history
                st.session_state.chat_history.append({
                    "question": question,
                    "figure": figure,
                    "data": result.data,
                    "explanation": explanation,
                })

            except Exception as e:
                st.error(f"Unexpected error: {e}")