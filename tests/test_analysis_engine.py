import pytest
from core.analysis_engine import AnalysisEngine
from models.analysis_step import AnalysisStep
from models.execution_plan import ExecutionPlan, VisualizationConfig


def make_plan(steps: list[dict], chart: str = "bar") -> ExecutionPlan:
    return ExecutionPlan(
        steps=[AnalysisStep(**s) for s in steps],
        visualization=VisualizationConfig(chart_type=chart),
    )


class TestAnalysisEngineInOperator:
    """Tests for the 'in' filter operator in AnalysisEngine."""

    def test_filter_in_multiple_values(self, superstore_df):
        engine = AnalysisEngine()
        plan = make_plan([
            {"operation": "filter", "column": "Category", "operator": "in", "value": ["Technology", "Furniture"]},
        ])
        result = engine.execute(superstore_df, plan, "Test in operator")
        assert result.success is True
        assert result.row_count == 7
        categories = {row["Category"] for row in result.data}
        assert categories == {"Technology", "Furniture"}

    def test_filter_in_single_item_list(self, superstore_df):
        engine = AnalysisEngine()
        plan = make_plan([
            {"operation": "filter", "column": "Region", "operator": "in", "value": ["West"]},
        ])
        result = engine.execute(superstore_df, plan, "Test single item in")
        assert result.success is True
        assert result.row_count == 3
        for row in result.data:
            assert row["Region"] == "West"

    def test_filter_in_nonexistent_value_returns_empty(self, superstore_df):
        engine = AnalysisEngine()
        plan = make_plan([
            {"operation": "filter", "column": "Category", "operator": "in", "value": ["NonExistent"]},
        ])
        result = engine.execute(superstore_df, plan, "Test nonexistent value")
        assert result.success is True
        assert result.row_count == 0

    def test_filter_in_with_numeric_values(self, superstore_df):
        engine = AnalysisEngine()
        plan = make_plan([
            {"operation": "filter", "column": "Sales", "operator": "in", "value": [500.0, 200.0]},
        ])
        result = engine.execute(superstore_df, plan, "Test numeric in")
        assert result.success is True
        assert result.row_count == 2
        sales_values = {row["Sales"] for row in result.data}
        assert sales_values == {500.0, 200.0}

    def test_existing_equals_operator_still_works(self, superstore_df):
        engine = AnalysisEngine()
        plan = make_plan([
            {"operation": "filter", "column": "Region", "operator": "=", "value": "West"},
        ])
        result = engine.execute(superstore_df, plan, "Test equals regression")
        assert result.success is True
        assert result.row_count == 3

    def test_existing_contains_operator_still_works(self, superstore_df):
        engine = AnalysisEngine()
        plan = make_plan([
            {"operation": "filter", "column": "Region", "operator": "contains", "value": "est"},
        ])
        result = engine.execute(superstore_df, plan, "Test contains regression")
        assert result.success is True
        regions = {row["Region"] for row in result.data}
        assert "West" in regions

    def test_existing_year_equals_still_works(self, superstore_df):
        engine = AnalysisEngine()
        plan = make_plan([
            {"operation": "filter", "column": "Order Date", "operator": "year_equals", "value": 2023},
        ])
        result = engine.execute(superstore_df, plan, "Test year_equals regression")
        assert result.success is True
        assert result.row_count == 6