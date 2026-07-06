"""
tests/test_explanation_engine.py

Lightweight verification for ExplanationEngine.
Uses monkeypatching to avoid real API calls.
Run: pytest tests/test_explanation_engine.py -v
"""

import pytest
from unittest.mock import MagicMock

from core.explanation_engine import ExplanationEngine
from models.analysis_result import AnalysisResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_engine_with_mock_response(mock_text: str) -> ExplanationEngine:
    """Return an ExplanationEngine whose AIClient always returns mock_text."""
    engine = ExplanationEngine()
    engine.client = MagicMock()
    engine.client.ask.return_value = mock_text
    return engine


def assert_has_all_sections(text: str):
    """Verify the 4 required section headers are present."""
    assert "## Executive Summary" in text, f"Missing Executive Summary in:\n{text}"
    assert "## Key Insights" in text, f"Missing Key Insights in:\n{text}"
    assert "## Business Interpretation" in text, f"Missing Business Interpretation in:\n{text}"
    assert "## Recommended Actions" in text, f"Missing Recommended Actions in:\n{text}"


# ---------------------------------------------------------------------------
# 1. KPI Explanation
# ---------------------------------------------------------------------------

class TestKPIExplanation:

    def test_kpi_generates_all_sections(self):
        result = AnalysisResult(
            success=True,
            question="What is total sales?",
            data=[{"Sales": 125000.0, "aggregation": "sum"}],
            row_count=1,
            columns=["Sales", "aggregation"],
            execution_steps_run=1,
        )
        engine = make_engine_with_mock_response(
            "## Executive Summary\n"
            "Total sales reached $125,000.\n\n"
            "## Key Insights\n"
            "- Total sales: $125,000\n"
            "- Aggregation method: sum\n\n"
            "## Business Interpretation\n"
            "The business generated $125,000 in total sales.\n\n"
            "## Recommended Actions\n"
            "Review sales performance against targets."
        )
        text = engine.explain(result)
        assert_has_all_sections(text)

    def test_kpi_uses_actual_value(self):
        result = AnalysisResult(
            success=True,
            question="What is total profit?",
            data=[{"Profit": 34200.0, "aggregation": "sum"}],
            row_count=1,
            columns=["Profit", "aggregation"],
            execution_steps_run=1,
        )
        engine = make_engine_with_mock_response(
            "## Executive Summary\n"
            "Total profit is $34,200.\n\n"
            "## Key Insights\n"
            "- Profit totals $34,200\n\n"
            "## Business Interpretation\n"
            "Profit generation stands at $34,200.\n\n"
            "## Recommended Actions\n"
            "Monitor profit margins closely."
        )
        text = engine.explain(result)
        assert "34200" in text or "$34,200" in text or "34,200" in text


# ---------------------------------------------------------------------------
# 2. Aggregation / Group-by Explanation
# ---------------------------------------------------------------------------

class TestAggregationExplanation:

    def test_group_by_aggregation_generates_all_sections(self):
        result = AnalysisResult(
            success=True,
            question="Show sales by region",
            data=[
                {"Region": "West", "Sales": 50000.0},
                {"Region": "East", "Sales": 35000.0},
                {"Region": "Central", "Sales": 25000.0},
            ],
            row_count=3,
            columns=["Region", "Sales"],
            execution_steps_run=3,
        )
        engine = make_engine_with_mock_response(
            "## Executive Summary\n"
            "West leads with $50,000 in sales, followed by East at $35,000.\n\n"
            "## Key Insights\n"
            "- West: $50,000 (highest)\n"
            "- East: $35,000\n"
            "- Central: $25,000 (lowest)\n\n"
            "## Business Interpretation\n"
            "West region outperforms others by a significant margin.\n\n"
            "## Recommended Actions\n"
            "Investigate West region strategies for replication."
        )
        text = engine.explain(result)
        assert_has_all_sections(text)


# ---------------------------------------------------------------------------
# 3. Time-Series Explanation
# ---------------------------------------------------------------------------

class TestTimeSeriesExplanation:

    def test_time_series_generates_all_sections(self):
        result = AnalysisResult(
            success=True,
            question="Show monthly sales trend",
            data=[
                {"Order Date": "2023-01", "Sales": 10000.0},
                {"Order Date": "2023-02", "Sales": 12000.0},
                {"Order Date": "2023-03", "Sales": 11500.0},
            ],
            row_count=3,
            columns=["Order Date", "Sales"],
            execution_steps_run=2,
        )
        engine = make_engine_with_mock_response(
            "## Executive Summary\n"
            "Sales trended upward from $10,000 to $12,000 over three months.\n\n"
            "## Key Insights\n"
            "- January: $10,000\n"
            "- February: $12,000 (peak)\n"
            "- March: $11,500 (slight decline)\n\n"
            "## Business Interpretation\n"
            "Sales grew 20% from January to February before moderating in March.\n\n"
            "## Recommended Actions\n"
            "Investigate March decline and sustain February growth drivers."
        )
        text = engine.explain(result)
        assert_has_all_sections(text)


# ---------------------------------------------------------------------------
# 4. Distribution Explanation
# ---------------------------------------------------------------------------

class TestDistributionExplanation:

    def test_distribution_generates_all_sections(self):
        result = AnalysisResult(
            success=True,
            question="Show category distribution",
            data=[
                {"Category": "Technology", "count": 450},
                {"Category": "Furniture", "count": 320},
                {"Category": "Office Supplies", "count": 230},
            ],
            row_count=3,
            columns=["Category", "count"],
            execution_steps_run=1,
        )
        engine = make_engine_with_mock_response(
            "## Executive Summary\n"
            "Technology dominates with 450 records, nearly half the dataset.\n\n"
            "## Key Insights\n"
            "- Technology: 450 records\n"
            "- Furniture: 320 records\n"
            "- Office Supplies: 230 records\n\n"
            "## Business Interpretation\n"
            "Technology products represent the largest segment.\n\n"
            "## Recommended Actions\n"
            "Ensure adequate inventory for Technology products."
        )
        text = engine.explain(result)
        assert_has_all_sections(text)


# ---------------------------------------------------------------------------
# 5. Correlation Explanation
# ---------------------------------------------------------------------------

class TestCorrelationExplanation:

    def test_correlation_generates_all_sections(self):
        result = AnalysisResult(
            success=True,
            question="Show correlation matrix",
            data=[
                {"column": "Sales", "Profit": 0.85, "Discount": -0.42},
                {"column": "Profit", "Sales": 0.85, "Discount": -0.67},
            ],
            row_count=2,
            columns=["column", "Sales", "Profit", "Discount"],
            execution_steps_run=1,
        )
        engine = make_engine_with_mock_response(
            "## Executive Summary\n"
            "Sales and Profit show strong positive correlation (0.85).\n\n"
            "## Key Insights\n"
            "- Sales-Profit correlation: 0.85 (strong positive)\n"
            "- Sales-Discount correlation: -0.42 (moderate negative)\n\n"
            "## Business Interpretation\n"
            "Higher sales consistently accompany higher profits.\n\n"
            "## Recommended Actions\n"
            "Focus on sales growth initiatives to drive profit."
        )
        text = engine.explain(result)
        assert_has_all_sections(text)


# ---------------------------------------------------------------------------
# 6. Empty Dataset
# ---------------------------------------------------------------------------

class TestEmptyDataset:

    def test_empty_data_returns_professional_message(self):
        result = AnalysisResult(
            success=True,
            question="Show top 10 products",
            data=[],
            row_count=0,
            columns=[],
            execution_steps_run=1,
        )
        engine = ExplanationEngine()
        text = engine.explain(result)
        assert_has_all_sections(text)
        assert "insufficient" in text.lower() or "no data" in text.lower()


# ---------------------------------------------------------------------------
# 7. Failed Analysis
# ---------------------------------------------------------------------------

class TestFailedAnalysis:

    def test_failed_result_returns_error_message(self):
        result = AnalysisResult(
            success=False,
            question="Invalid question",
            error="Column 'Revenue' not found in dataset.",
            execution_steps_run=0,
        )
        engine = ExplanationEngine()
        text = engine.explain(result)
        assert "could not be completed" in text
        assert "Revenue" in text