import streamlit as st
import pandas as pd

from core.data_loader import load_csv
from core.data_validator import validate_dataframe
from core.data_cleaner import DataCleaner
from core.data_profiler import DataProfiler

# ---------------------------------
# Page Configuration
# ---------------------------------
st.set_page_config(
    page_title="AI BI Assistant",
    page_icon="📊",
    layout="wide"
)

# ---------------------------------
# Title
# ---------------------------------
st.title("📊 AI BI Assistant")
st.write("Upload your CSV file to begin analysis.")

# ---------------------------------
# Sidebar
# ---------------------------------
st.sidebar.title("Navigation")
st.sidebar.write("Welcome to AI BI Assistant")

# ---------------------------------
# File Upload
# ---------------------------------
uploaded_file = st.file_uploader(
    "Upload your CSV File",
    type=["csv"]
)

# ---------------------------------
# Main Workflow
# ---------------------------------
if uploaded_file is not None:

    # Load CSV
    success, result = load_csv(uploaded_file)

    if success:

        df = result

        # Validate DataFrame
        status, message = validate_dataframe(df)

        if status:

            st.success(message)

            # Clean Data
            cleaner = DataCleaner()
            df, report = cleaner.clean(df)
            
            # Profile Dataset
            profiler = DataProfiler()
            profile = profiler.profile(df)

            # -----------------------------
            # Dataset Preview
            # -----------------------------
            st.subheader("📊 Dataset Preview")
            st.dataframe(df)

            # -----------------------------
            # Data Cleaning Report
            # -----------------------------
            st.subheader("🧹 Data Cleaning Report")

            # -----------------------------
            # Dataset Profile
            # -----------------------------
            st.subheader("📋 Dataset Profile")

            col1, col2 = st.columns(2)

            with col1:
                st.metric("Rows", profile["rows"])
                st.metric("Columns", profile["columns"])

            with col2:
                st.write("### Date Columns")
                if profile["date_columns"]:
                    st.write(profile["date_columns"])
                else:
                    st.write("No date columns")

            st.write("### Numeric Columns")
            st.write(profile["numeric_columns"])

            st.write("### Categorical Columns")
            st.write(profile["categorical_columns"])

            st.write("### Column Names")
            st.write(profile["column_names"])

            # Missing Values
            st.write("### Missing Values")

            if report["missing_values"]:

                missing_df = pd.DataFrame(
                    report["missing_values"].items(),
                    columns=["Column", "Missing Values"]
                )

                st.dataframe(missing_df)

            else:
                st.success("No missing values found.")

            # Duplicates
            st.write("### Duplicates Removed")
            st.write(report["duplicates_removed"])

            # Date Columns
            st.write("### Date Columns Detected")

            if report["date_columns"]:
                st.write(report["date_columns"])
            else:
                st.info("No date columns detected.")

        else:
            st.error(message)

    else:
        st.error(result)

else:
    st.info("Please upload a CSV file.")