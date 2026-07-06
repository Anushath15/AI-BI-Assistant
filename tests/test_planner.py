"""
tests/test_planner.py

Comprehensive planner test suite for the 15 demo business questions.

Run from project root:
    python tests/test_planner.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from typing import List, Dict, Any, Tuple

from core.command_validator import CommandValidator
from models.dataset_profile import DatasetProfile


# =============================================================================
# DEMO DATASET PROFILE (matches actual project model)
# =============================================================================

DEMO_PROFILE = DatasetProfile(
    rows=9994,
    columns=21,
    column_names=[
        "Row ID", "Order ID", "Order Date", "Ship Date", "Ship Mode",
        "Customer Name", "Segment", "Country", "City", "State",
        "Postal Code", "Region", "Product ID", "Category", "Sub-Category",
        "Product Name", "Sales", "Quantity", "Discount", "Profit",
        "Order Priority"
    ],
    data_types={
        "Row ID": "int64", "Order ID": "object", "Order Date": "datetime64[ns]",
        "Ship Date": "datetime64[ns]", "Ship Mode": "object", "Customer Name": "object",
        "Segment": "object", "Country": "object", "City": "object", "State": "object",
        "Postal Code": "int64", "Region": "object", "Product ID": "object",
        "Category": "object", "Sub-Category": "object", "Product Name": "object",
        "Sales": "float64", "Quantity": "int64", "Discount": "float64",
        "Profit": "float64", "Order Priority": "object"
    },
    numeric_columns=["Sales", "Quantity", "Discount", "Profit", "Row ID", "Postal Code"],
    categorical_columns=[
        "Order ID", "Ship Mode", "Customer Name", "Segment", "Country", "City",
        "State", "Region", "Product ID", "Category", "Sub-Category",
        "Product Name", "Order Priority"
    ],
    date_columns=["Order Date", "Ship Date"],
    missing_values={},
    sample_data=[
        {"Order Date": "2023-01-03", "Customer Name": "Claire Gute", "Region": "South", "Category": "Furniture", "Sales": 261.96, "Profit": 41.91},
        {"Order Date": "2023-01-05", "Customer Name": "Darrin Van Huff", "Region": "West", "Category": "Office Supplies", "Sales": 755.96, "Profit": 113.39},
        {"Order Date": "2023-01-08", "Customer Name": "Sean O\'Donnell", "Region": "West", "Category": "Office Supplies", "Sales": 22.36, "Profit": 2.52},
    ],
)


# =============================================================================
# EXPECTED PLANS FOR 15 DEMO QUESTIONS
# =============================================================================

DEMO_QUESTIONS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "question": "Total Sales",
        "expected_plan": {
            "steps": [
                {"operation": "kpi", "metric": "Sales", "aggregation": "sum"}
            ],
            "visualization": {"chart_type": "table", "title": "Total Sales"}
        },
    },
    {
        "id": 2,
        "question": "Total Profit",
        "expected_plan": {
            "steps": [
                {"operation": "kpi", "metric": "Profit", "aggregation": "sum"}
            ],
            "visualization": {"chart_type": "table", "title": "Total Profit"}
        },
    },
    {
        "id": 3,
        "question": "Sales by Region",
        "expected_plan": {
            "steps": [
                {"operation": "group_by", "column": "Region"},
                {"operation": "aggregate", "metric": "Sales", "aggregation": "sum"},
                {"operation": "sort", "column": "Sales", "order": "descending"},
            ],
            "visualization": {"chart_type": "bar", "x_axis": "Region", "y_axis": "Sales", "title": "Sales by Region"}
        },
    },
    {
        "id": 4,
        "question": "Profit by Category",
        "expected_plan": {
            "steps": [
                {"operation": "group_by", "column": "Category"},
                {"operation": "aggregate", "metric": "Profit", "aggregation": "sum"},
                {"operation": "sort", "column": "Profit", "order": "descending"},
            ],
            "visualization": {"chart_type": "bar", "x_axis": "Category", "y_axis": "Profit", "title": "Profit by Category"}
        },
    },
    {
        "id": 5,
        "question": "Top 10 Customers by Sales",
        "expected_plan": {
            "steps": [
                {"operation": "group_by", "column": "Customer Name"},
                {"operation": "aggregate", "metric": "Sales", "aggregation": "sum"},
                {"operation": "sort", "column": "Sales", "order": "descending"},
                {"operation": "limit", "n": 10},
            ],
            "visualization": {"chart_type": "bar", "x_axis": "Customer Name", "y_axis": "Sales", "title": "Top 10 Customers by Sales"}
        },
    },
    {
        "id": 6,
        "question": "Bottom 5 Products by Profit",
        "expected_plan": {
            "steps": [
                {"operation": "group_by", "column": "Product Name"},
                {"operation": "aggregate", "metric": "Profit", "aggregation": "sum"},
                {"operation": "sort", "column": "Profit", "order": "ascending"},
                {"operation": "limit", "n": 5},
            ],
            "visualization": {"chart_type": "bar", "x_axis": "Product Name", "y_axis": "Profit", "title": "Bottom 5 Products by Profit"}
        },
    },
    {
        "id": 7,
        "question": "Monthly Sales Trend",
        "expected_plan": {
            "steps": [
                {"operation": "time_series", "column": "Order Date", "metric": "Sales"},
            ],
            "visualization": {"chart_type": "line", "x_axis": "Order Date", "y_axis": "Sales", "title": "Monthly Sales Trend"}
        },
    },
    {
        "id": 8,
        "question": "Sales in 2023",
        "expected_plan": {
            "steps": [
                {"operation": "filter", "column": "Order Date", "operator": "year_equals", "value": 2023},
                {"operation": "group_by", "column": "Category"},
                {"operation": "aggregate", "metric": "Sales", "aggregation": "sum"},
                {"operation": "sort", "column": "Sales", "order": "descending"},
            ],
            "visualization": {"chart_type": "bar", "x_axis": "Category", "y_axis": "Sales", "title": "Sales in 2023"}
        },
    },
    {
        "id": 9,
        "question": "Technology Sales",
        "expected_plan": {
            "steps": [
                {"operation": "filter", "column": "Category", "operator": "=", "value": "Technology"},
                {"operation": "group_by", "column": "Sub-Category"},
                {"operation": "aggregate", "metric": "Sales", "aggregation": "sum"},
                {"operation": "sort", "column": "Sales", "order": "descending"},
            ],
            "visualization": {"chart_type": "bar", "x_axis": "Sub-Category", "y_axis": "Sales", "title": "Technology Sales"}
        },
    },
    {
        "id": 10,
        "question": "Compare Regions",
        "expected_plan": {
            "steps": [
                {"operation": "group_by", "column": "Region"},
                {"operation": "aggregate", "metric": "Sales", "aggregation": "sum"},
                {"operation": "sort", "column": "Sales", "order": "descending"},
            ],
            "visualization": {"chart_type": "bar", "x_axis": "Region", "y_axis": "Sales", "title": "Sales by Region"}
        },
    },
    {
        "id": 11,
        "question": "Category Distribution",
        "expected_plan": {
            "steps": [
                {"operation": "distribution", "column": "Category"},
            ],
            "visualization": {"chart_type": "pie", "x_axis": "Category", "y_axis": "count", "title": "Category Distribution"}
        },
    },
    {
        "id": 12,
        "question": "Correlation between Sales and Profit",
        "expected_plan": {
            "steps": [
                {"operation": "correlation"},
            ],
            "visualization": {"chart_type": "table", "title": "Correlation between Sales and Profit"}
        },
    },
    {
        "id": 13,
        "question": "Monthly Profit Trend",
        "expected_plan": {
            "steps": [
                {"operation": "time_series", "column": "Order Date", "metric": "Profit"},
            ],
            "visualization": {"chart_type": "line", "x_axis": "Order Date", "y_axis": "Profit", "title": "Monthly Profit Trend"}
        },
    },
    {
        "id": 14,
        "question": "Sales in West Region",
        "expected_plan": {
            "steps": [
                {"operation": "filter", "column": "Region", "operator": "=", "value": "West"},
                {"operation": "group_by", "column": "Category"},
                {"operation": "aggregate", "metric": "Sales", "aggregation": "sum"},
                {"operation": "sort", "column": "Sales", "order": "descending"},
            ],
            "visualization": {"chart_type": "bar", "x_axis": "Category", "y_axis": "Sales", "title": "Sales in West Region"}
        },
    },
    {
        "id": 15,
        "question": "Average Discount",
        "expected_plan": {
            "steps": [
                {"operation": "kpi", "metric": "Discount", "aggregation": "mean"}
            ],
            "visualization": {"chart_type": "table", "title": "Average Discount"}
        },
    },
]


# =============================================================================
# FAILURE MODE TESTS (bad plans the old prompt might generate)
# =============================================================================

FAILURE_MODE_QUESTIONS: List[Dict[str, Any]] = [
    {
        "id": "F1",
        "question": "Forecast next 3 months",
        "bad_plan": {"steps": [{"operation": "forecast", "column": "Order Date", "metric": "Sales"}], "visualization": {"chart_type": "line", "title": "Forecast"}},
    },
    {
        "id": "F2",
        "question": "Sales in 2023",
        "bad_plan": {"steps": [{"operation": "filter", "column": "Order Date", "operator": "in", "value": [2023]}], "visualization": {"chart_type": "bar", "title": "Sales"}},
    },
    {
        "id": "F3",
        "question": "Sales between 1000 and 5000",
        "bad_plan": {"steps": [{"operation": "filter", "column": "Sales", "operator": "between", "value": [1000, 5000]}], "visualization": {"chart_type": "bar", "title": "Sales"}},
    },
    {
        "id": "F4",
        "question": "Sales last year",
        "bad_plan": {"steps": [{"operation": "filter", "column": "Order Date", "operator": "last_year"}], "visualization": {"chart_type": "bar", "title": "Sales"}},
    },
    {
        "id": "F5",
        "question": "Rolling average of sales",
        "bad_plan": {"steps": [{"operation": "rolling_average", "column": "Order Date", "metric": "Sales"}], "visualization": {"chart_type": "line", "title": "Rolling Average"}},
    },
    {
        "id": "F6",
        "question": "Top 10 customers by sales",
        "bad_plan": {"steps": [{"operation": "top_n", "n": 10}], "visualization": {"chart_type": "bar", "title": "Top 10"}},
    },
    {
        "id": "F7",
        "question": "Compare regions",
        "bad_plan": {"steps": [{"operation": "compare", "column": "Region"}], "visualization": {"chart_type": "bar", "title": "Compare"}},
    },
    {
        "id": "F8",
        "question": "Time series with group_by",
        "bad_plan": {"steps": [{"operation": "group_by", "column": "Region"}, {"operation": "time_series", "column": "Order Date", "metric": "Sales"}, {"operation": "aggregate", "metric": "Sales", "aggregation": "sum"}], "visualization": {"chart_type": "line", "title": "Time Series"}},
    },
    {
        "id": "F9",
        "question": "Growth by region",
        "bad_plan": {"steps": [{"operation": "growth", "column": "Region", "metric": "Sales"}], "visualization": {"chart_type": "bar", "title": "Growth"}},
    },
    {
        "id": "F10",
        "question": "Percentage change in sales",
        "bad_plan": {"steps": [{"operation": "percentage_change", "column": "Order Date", "metric": "Sales"}], "visualization": {"chart_type": "line", "title": "Percentage Change"}},
    },
]


# =============================================================================
# TEST RUNNER
# =============================================================================

def run_planner_tests() -> Tuple[List[Dict], List[Dict]]:
    validator = CommandValidator()
    passed = []
    failed = []

    for test_case in DEMO_QUESTIONS:
        plan_json = json.dumps(test_case["expected_plan"])
        result = validator.validate(plan_json, DEMO_PROFILE, original_question=test_case["question"])
        ok = result.success

        if ok:
            passed.append({
                "id": test_case["id"],
                "question": test_case["question"],
            })
        else:
            failed.append({
                "id": test_case["id"],
                "question": test_case["question"],
                "error": result.error,
                "expected_plan": test_case["expected_plan"],
            })

    return passed, failed


def run_failure_mode_tests() -> Tuple[List[Dict], List[Dict]]:
    validator = CommandValidator()
    rejected = []
    passed_bad = []

    for test_case in FAILURE_MODE_QUESTIONS:
        plan_json = json.dumps(test_case["bad_plan"])
        result = validator.validate(plan_json, DEMO_PROFILE, original_question=test_case["question"])
        ok = result.success

        if not ok:
            rejected.append({
                "id": test_case["id"],
                "question": test_case["question"],
                "error": result.error,
            })
        else:
            passed_bad.append({
                "id": test_case["id"],
                "question": test_case["question"],
                "plan": test_case["bad_plan"],
            })

    return rejected, passed_bad


def print_test_report(passed: List[Dict], failed: List[Dict], rejected: List[Dict], passed_bad: List[Dict]):
    total = len(passed) + len(failed)
    total_bad = len(rejected) + len(passed_bad)

    print("=" * 70)
    print("PLANNER TEST REPORT")
    print("=" * 70)
    print(f"\nDEMO QUESTIONS (Expected Plans):")
    print(f"  Total: {total}")
    print(f"  Passed: {len(passed)} ({len(passed)/total*100:.1f}%)")
    print(f"  Failed: {len(failed)} ({len(failed)/total*100:.1f}%)")

    if passed:
        print("\n  ✅ PASSED:")
        for p in passed:
            print(f"    [{p['id']:2d}] {p['question']}")

    if failed:
        print("\n  ❌ FAILED:")
        for f in failed:
            print(f"    [{f['id']:2d}] {f['question']}")
            print(f"         Error: {f['error']}")

    print(f"\nFAILURE MODES (Bad Plans):")
    print(f"  Total: {total_bad}")
    print(f"  Correctly Rejected: {len(rejected)} ({len(rejected)/total_bad*100:.1f}%)")
    print(f"  Incorrectly Passed: {len(passed_bad)} ({len(passed_bad)/total_bad*100:.1f}%)")

    if rejected:
        print("\n  ✅ CORRECTLY REJECTED:")
        for r in rejected:
            print(f"    [{r['id']}] {r['question']}")
            print(f"         Error: {r['error'][:80]}...")

    if passed_bad:
        print("\n  ⚠️  INCORRECTLY PASSED (Semantic issues — prompt must prevent these):")
        for pb in passed_bad:
            print(f"    [{pb['id']}] {pb['question']}")
            print(f"         Plan: {json.dumps(pb['plan'], indent=8)}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    passed, failed = run_planner_tests()
    rejected, passed_bad = run_failure_mode_tests()
    print_test_report(passed, failed, rejected, passed_bad)