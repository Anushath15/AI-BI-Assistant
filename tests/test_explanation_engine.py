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


def make_engine_with_mock_response(mock_text: str) -> ExplanationEngine:
    engine = ExplanationEngine()
    engine.client = MagicMock()
    engine.client.ask.return_value = mock_text
    return engine


def assert_has_all_sections(text: str):
    assert "## Executive Summary" in text
    assert "## Key Insights" in text
    assert "## Business Interpretation" in text
    assert "## Recommended Actions" in text


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
            "## Executive Summary\nTotal sales reached ,000.\n\n## Key Insights\n- Total sales: ,000\n\n## Business Interpretation\nThe business generated ,000 in total sales.\n\n## Recommended Actions\nReview sales performance against targets."
        )
        text = engine.explain(result)
        assert_has_all_sections(text)


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
            "## Executive Summary\nWest leads with ,000.\n\n## Key Insights\n- West: ,000\n\n## Business Interpretation\nWest region outperforms others.\n\n## Recommended Actions\nInvestigate West region strategies."
        )
        text = engine.explain(result)
        assert_has_all_sections(text)


class TestTimeSeriesExplanation:
    def test_time_series_generates_all_sections(self):
        result = AnalysisResult(
            success=True,
            question="Show monthly sales trend",
            data=[
                {"Order Date": "2023-01", "Sales": 10000.0},
                {"Order Date": "2023-02", "Sales": 12000.0},
            ],
            row_count=2,
            columns=["Order Date", "Sales"],
            execution_steps_run=2,
        )
        engine = make_engine_with_mock_response(
            "## Executive Summary\nSales trended upward.\n\n## Key Insights\n- January: ,000\n\n## Business Interpretation\nSales grew over the period.\n\n## Recommended Actions\nInvestigate growth drivers."
        )
        text = engine.explain(result)
        assert_has_all_sections(text)


class TestDistributionExplanation:
    def test_distribution_generates_all_sections(self):
        result = AnalysisResult(
            success=True,
            question="Show category distribution",
            data=[
                {"Category": "Technology", "count": 450},
                {"Category": "Furniture", "count": 320},
            ],
            row_count=2,
            columns=["Category", "count"],
            execution_steps_run=1,
        )
        engine = make_engine_with_mock_response(
            "## Executive Summary\nTechnology dominates.\n\n## Key Insights\n- Technology: 450 records\n\n## Business Interpretation\nTechnology is the largest segment.\n\n## Recommended Actions\nEnsure adequate inventory."
        )
        text = engine.explain(result)
        assert_has_all_sections(text)


class TestCorrelationExplanation:
    def test_correlation_generates_all_sections(self):
        result = AnalysisResult(
            success=True,
            question="Show correlation matrix",
            data=[
                {"column": "Sales", "Profit": 0.85},
            ],
            row_count=1,
            columns=["column", "Sales", "Profit"],
            execution_steps_run=1,
        )
        engine = make_engine_with_mock_response(
            "## Executive Summary\nSales and Profit correlate strongly.\n\n## Key Insights\n- Correlation: 0.85\n\n## Business Interpretation\nHigher sales accompany higher profits.\n\n## Recommended Actions\nFocus on sales growth."
        )
        text = engine.explain(result)
        assert_has_all_sections(text)


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
