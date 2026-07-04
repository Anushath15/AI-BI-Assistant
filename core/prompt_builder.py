import json
from models.dataset_profile import DatasetProfile
from utils.constants import (
    SUPPORTED_OPERATIONS,
    SUPPORTED_AGGREGATIONS,
    SUPPORTED_CHARTS,
    SUPPORTED_FILTER_OPERATORS,
)

SYSTEM_PROMPT = """You are an AI Business Intelligence Planner.

Your ONLY job is to convert a business question into a structured JSON execution plan.

Rules:
- Never answer the question directly.
- Never generate Python, SQL, or any code.
- Never explain your reasoning.
- Never invent column names. Use ONLY columns from the dataset schema.
- Always return valid JSON. Nothing else. No markdown. No backticks.
- Every step must use only supported operations.

The JSON must follow this exact format:
{
    "steps": [
        {"operation": "filter", "column": "Order Date", "operator": "year_equals", "value": 2024},
        {"operation": "group_by", "column": "Product Name"},
        {"operation": "aggregate", "metric": "Sales", "aggregation": "sum"},
        {"operation": "sort", "column": "Sales", "order": "descending"},
        {"operation": "limit", "n": 10}
    ],
    "visualization": {
        "chart_type": "bar",
        "x_axis": "Product Name",
        "y_axis": "Sales",
        "title": "Top 10 Products by Sales in 2024"
    }
}

For time series questions, always include both column and metric:
{"operation": "time_series", "column": "Order Date", "metric": "Sales"}"""


class PromptBuilder:

    def build(self, profile: DatasetProfile, question: str) -> tuple[str, str]:

        safe_sample = [
            {k: str(v) for k, v in row.items()}
            for row in profile.sample_data
        ]

        context = {
            "rows": profile.rows,
            "column_names": profile.column_names,
            "data_types": profile.data_types,
            "numeric_columns": profile.numeric_columns,
            "categorical_columns": profile.categorical_columns,
            "date_columns": profile.date_columns,
            "sample_data": safe_sample[:3],
            "supported_operations": SUPPORTED_OPERATIONS,
            "supported_aggregations": SUPPORTED_AGGREGATIONS,
            "supported_charts": SUPPORTED_CHARTS,
            "supported_filter_operators": SUPPORTED_FILTER_OPERATORS,
        }

        user_prompt = f"""Dataset Schema:
{json.dumps(context, indent=2)}

Business Question:
{question}

Return ONLY the JSON execution plan. No explanation. No markdown."""

        return SYSTEM_PROMPT, user_prompt