import json
import pandas as pd
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from models.dataset_profile import DatasetProfile
from models.execution_plan import ExecutionPlan, VisualizationConfig
from models.analysis_step import AnalysisStep
from core.command_validator import CommandValidator
from core.analysis_engine import AnalysisEngine


# ---------------------------------------------------------------------------
# Pure helper functions (not pytest fixtures — imported directly in tests)
# ---------------------------------------------------------------------------

def make_profile(**overrides) -> DatasetProfile:
    """
    Build a DatasetProfile that matches SUPERSTORE_DF exactly.

    Accepts keyword overrides so individual tests can mutate a single field
    without re-specifying the entire structure. This is the same pattern used
    in test_business_knowledge.py — keep it consistent.

    Example:
        make_profile(numeric_columns=[])          # strip numeric cols
        make_profile(column_names=["X", "Y"])     # completely different schema
    """
    defaults = dict(
        rows=10,
        columns=5,
        column_names=["Region", "Category", "Sales", "Profit", "Order Date"],
        data_types={
            "Region":     "object",
            "Category":   "object",
            "Sales":      "float64",
            "Profit":     "float64",
            "Order Date": "datetime64[ns]",
        },
        numeric_columns=["Sales", "Profit"],
        categorical_columns=["Region", "Category"],
        date_columns=["Order Date"],
        missing_values={},
        sample_data=[
            {
                "Region": "West", "Category": "Technology",
                "Sales": 500.0, "Profit": 120.0,
                "Order Date": "2022-01-15",
            }
        ],
    )
    defaults.update(overrides)
    return DatasetProfile(**defaults)


def make_plan(steps: list[dict], chart: str = "bar") -> ExecutionPlan:
    """
    Build an ExecutionPlan from a list of raw step dicts.

    Reuses the same signature as the helper in test_conversation_context.py
    so both files stay in sync if the model ever changes.

    Example:
        make_plan([
            {"operation": "group_by",  "column": "Region"},
            {"operation": "aggregate", "metric": "Sales", "aggregation": "sum"},
        ])
    """
    return ExecutionPlan(
        steps=[AnalysisStep(**s) for s in steps],
        visualization=VisualizationConfig(chart_type=chart),
    )


def make_valid_raw_response(steps: list[dict], chart: str = "bar") -> str:
    """
    Serialize a list of step dicts into the JSON string that Groq would return,
    so CommandValidator tests can test the full pipeline from raw string to plan.

    Example:
        raw = make_valid_raw_response([
            {"operation": "kpi", "metric": "Sales", "aggregation": "sum"},
        ])
        ok, plan = CommandValidator().validate(raw, make_profile())
    """
    payload = {
        "steps": steps,
        "visualization": {"chart_type": chart},
    }
    return json.dumps(payload)


# ---------------------------------------------------------------------------
# The canonical in-memory DataFrame used by AnalysisEngine tests
# ---------------------------------------------------------------------------
#
# Why exactly these rows?
#
#   Region distribution  : West×3, East×3, Central×2, South×2
#   Category distribution: Technology×4, Furniture×3, Office Supplies×3
#   Year distribution    : 2022×4, 2023×6
#   Month 1 (January)   : rows 0, 3, 9  (3 rows)
#   Profit signs         : 8 positive, 2 negative (East/Furniture and one Central)
#
#   String filter cases:
#     contains("tech", case=False)  → matches all 4 "Technology" rows (case-insensitive)
#     startswith("Tech")            → matches all 4 "Technology" rows (case-SENSITIVE)
#     startswith("tech")            → matches ZERO rows (case-sensitive, documented asymmetry)
#     endswith("ogy")               → matches all 4 "Technology" rows (case-sensitive)
#
SUPERSTORE_DATA = {
    "Region":     ["West",    "East",     "Central",         "South",     "West",
                   "East",    "Central",  "South",           "West",      "East"],
    "Category":   ["Technology", "Furniture", "Office Supplies", "Technology", "Furniture",
                   "Technology", "Office Supplies", "Furniture", "Office Supplies", "Technology"],
    "Sales":      [500.0, 200.0, 150.0, 800.0, 350.0,
                   600.0, 100.0, 450.0, 250.0, 700.0],
    "Profit":     [120.0, -30.0, 45.0,  200.0,  80.0,
                   150.0,  25.0, 110.0,  60.0, 180.0],
    "Order Date": [
        "2022-01-15", "2022-03-20", "2022-07-10", "2023-01-05", "2023-04-12",
        "2023-08-22", "2023-09-15", "2022-11-30", "2023-02-14", "2023-01-19",
    ],
}


@pytest.fixture
def superstore_df() -> pd.DataFrame:
    """
    A small, deterministic Superstore-like DataFrame.

    Returned with 'Order Date' already parsed to datetime so that year_equals,
    month_equals, and time_series operations work without needing to coerce
    inside each test.

    Tests that need the date column as a raw string (to test coercion behaviour)
    should convert it themselves: df["Order Date"].astype(str).
    """
    df = pd.DataFrame(SUPERSTORE_DATA)
    df["Order Date"] = pd.to_datetime(df["Order Date"])
    return df


@pytest.fixture
def profile() -> DatasetProfile:
    """
    A DatasetProfile that exactly matches superstore_df.

    Tests that need a modified profile should call make_profile(**overrides)
    directly rather than mutating this fixture.
    """
    return make_profile()


@pytest.fixture
def validator() -> CommandValidator:
    """A fresh CommandValidator for each test — stateless, but isolated."""
    return CommandValidator()


@pytest.fixture
def engine() -> AnalysisEngine:
    """A fresh AnalysisEngine for each test — stateless, but isolated."""
    return AnalysisEngine()