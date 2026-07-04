"""
tests/test_conversation_context.py

Unit tests for ConversationContext.
Run with: pytest tests/test_conversation_context.py -v
"""

import pytest
from core.conversation_context import ConversationContext, ConversationTurn
from models.execution_plan import ExecutionPlan, VisualizationConfig
from models.analysis_step import AnalysisStep


def make_plan(steps: list[dict], chart: str = "bar") -> ExecutionPlan:
    return ExecutionPlan(
        steps=[AnalysisStep(**s) for s in steps],
        visualization=VisualizationConfig(chart_type=chart),
    )


class TestConversationContext:

    def test_initial_state_empty(self):
        ctx = ConversationContext()
        assert not ctx.has_context()
        assert ctx.get_context_summary() == ""

    def test_add_turn_records_question(self):
        ctx = ConversationContext()
        ctx.add_turn("What are total sales?")
        assert ctx.has_context()

    def test_context_summary_contains_question(self):
        ctx = ConversationContext()
        ctx.add_turn("What are total sales by region?")
        summary = ctx.get_context_summary()
        assert "total sales by region" in summary

    def test_extracts_group_by_from_plan(self):
        ctx = ConversationContext()
        plan = make_plan([
            {"operation": "group_by", "column": "Region"},
            {"operation": "aggregate", "metric": "Sales", "aggregation": "sum"},
        ])
        ctx.add_turn("Sales by region", plan)
        assert ctx.active_group_by == "Region"

    def test_extracts_metric_from_plan(self):
        ctx = ConversationContext()
        plan = make_plan([
            {"operation": "group_by", "column": "Region"},
            {"operation": "aggregate", "metric": "Sales", "aggregation": "sum"},
        ])
        ctx.add_turn("Sales by region", plan)
        assert ctx.active_metric == "Sales"

    def test_accumulates_filters(self):
        ctx = ConversationContext()
        plan1 = make_plan([
            {"operation": "filter", "column": "Order Date", "operator": "year_equals", "value": 2023},
        ])
        plan2 = make_plan([
            {"operation": "filter", "column": "Region", "operator": "=", "value": "West"},
        ])
        ctx.add_turn("2023 data", plan1)
        ctx.add_turn("West region", plan2)
        columns = [f["column"] for f in ctx.active_filters]
        assert "Order Date" in columns
        assert "Region" in columns

    def test_filter_same_column_replaces_not_duplicates(self):
        ctx = ConversationContext()
        plan1 = make_plan([
            {"operation": "filter", "column": "Region", "operator": "=", "value": "West"},
        ])
        plan2 = make_plan([
            {"operation": "filter", "column": "Region", "operator": "=", "value": "East"},
        ])
        ctx.add_turn("West", plan1)
        ctx.add_turn("East", plan2)
        region_filters = [f for f in ctx.active_filters if f["column"] == "Region"]
        assert len(region_filters) == 1
        assert region_filters[0]["value"] == "East"

    def test_rolling_window_max_turns(self):
        ctx = ConversationContext()
        for i in range(7):
            ctx.add_turn(f"Question {i}")
        assert len(ctx._turns) == ConversationContext.MAX_TURNS

    def test_clear_resets_state(self):
        ctx = ConversationContext()
        plan = make_plan([
            {"operation": "group_by", "column": "Region"},
            {"operation": "aggregate", "metric": "Sales", "aggregation": "sum"},
        ])
        ctx.add_turn("Sales by region", plan)
        ctx.clear()
        assert not ctx.has_context()
        assert ctx.active_group_by is None
        assert ctx.active_metric is None
        assert ctx.active_filters == []

    def test_result_summary_formatted_cleanly(self):
        ctx = ConversationContext()
        ctx.add_turn(
            "Top region",
            result_data=[{"Region": "West", "Sales": 739813.61}]
        )
        summary = ctx.get_context_summary()
        assert "West" in summary
        assert "739813" in summary