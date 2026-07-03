import json

from utils.constants import (
    SUPPORTED_OPERATIONS,
    SUPPORTED_AGGREGATIONS,
    SUPPORTED_CHARTS,
)


class PromptBuilder:
    """
    Builds a structured prompt for the AI model.

    The prompt contains:
    - Dataset schema
    - Dataset metadata
    - Supported operations
    - User question

    The AI must return ONLY valid JSON.
    """

    def build_prompt(self, profile, user_question):

        context = {
            "rows": profile["rows"],
            "columns": profile["column_names"],
            "data_types": profile["data_types"],
            "numeric_columns": profile["numeric_columns"],
            "categorical_columns": profile["categorical_columns"],
            "date_columns": profile["date_columns"],
            "supported_operations": SUPPORTED_OPERATIONS,
            "supported_aggregations": SUPPORTED_AGGREGATIONS,
            "supported_charts": SUPPORTED_CHARTS
        }

        prompt = f"""
You are an AI Business Intelligence Planner.

Your job is NOT to answer the user's question.

Your job is to convert the user's question into a structured analysis plan.

Dataset Information

{json.dumps(context, indent=4)}

User Question

{user_question}

Return ONLY valid JSON.

Required JSON format

{{
    "operation": "",
    "group_by": "",
    "metric": "",
    "aggregation": "",
    "filters": [],
    "sort": "",
    "limit": null,
    "chart": "",
    "x_axis": "",
    "y_axis": ""
}}

Rules

- Never generate Python code.
- Never explain your answer.
- Never invent column names.
- Use only the provided columns.
- Use only supported operations.
- Use only supported charts.
- Output must be valid JSON.
"""

        return prompt