"""
core/capability_registry.py

Single source of truth for all execution engine capabilities.

This module exposes plain constants (lists and dicts) that define:
- What operations the AnalysisEngine can execute
- What filter operators are supported
- What aggregations are supported
- What chart types can be rendered
- How business concepts map to operations
- Common plan templates
- Negative examples (what NOT to generate)

All other modules (PromptBuilder, CommandValidator, AnalysisEngine)
import from here to ensure zero duplication and single-point-of-truth.

Backward compatibility: utils/constants.py re-exports from this module.
"""

# =============================================================================
# CORE CAPABILITIES — what the engine can actually execute
# =============================================================================

SUPPORTED_OPERATIONS = [
    "filter",
    "group_by",
    "aggregate",
    "sort",
    "limit",
    "time_series",
    "distribution",
    "correlation",
    "kpi",
    "top_n",
    "bottom_n",
    "compare",
]

SUPPORTED_AGGREGATIONS = [
    "sum",
    "mean",
    "count",
    "min",
    "max",
    "median",
    "std",
]

SUPPORTED_FILTER_OPERATORS = [
    "=",
    "!=",
    ">",
    "<",
    ">=",
    "<=",
    "contains",
    "startswith",
    "endswith",
    "year_equals",
    "month_equals",
]

SUPPORTED_CHART_TYPES = [
    "bar",
    "line",
    "pie",
    "scatter",
    "histogram",
    "box",
    "table",
]

# =============================================================================
# CONCEPT MAPPING — business language → operations
# =============================================================================

CONCEPT_MAPPING = {
    # Rankings
    "best": {"operation": "sort", "order": "descending", "note": "Use with limit"},
    "top": {"operation": "sort", "order": "descending", "note": "Use with limit"},
    "highest": {"operation": "sort", "order": "descending", "note": "Use with limit"},
    "maximum": {"operation": "sort", "order": "descending", "note": "Use with limit"},
    "worst": {"operation": "sort", "order": "ascending", "note": "Use with limit"},
    "lowest": {"operation": "sort", "order": "ascending", "note": "Use with limit"},
    "minimum": {"operation": "sort", "order": "ascending", "note": "Use with limit"},
    "bottom": {"operation": "sort", "order": "ascending", "note": "Use with limit"},

    # Aggregations
    "total": {"aggregation": "sum"},
    "sum": {"aggregation": "sum"},
    "average": {"aggregation": "mean"},
    "mean": {"aggregation": "mean"},
    "count": {"aggregation": "count"},
    "how many": {"aggregation": "count"},
    "number of": {"aggregation": "count"},
    "maximum value": {"aggregation": "max"},
    "minimum value": {"aggregation": "min"},
    "median": {"aggregation": "median"},
    "standard deviation": {"aggregation": "std"},

    # Analysis types
    "trend": {"operation": "time_series", "note": "Requires date column + metric"},
    "over time": {"operation": "time_series", "note": "Requires date column + metric"},
    "monthly": {"operation": "time_series", "note": "Groups by month automatically"},
    "breakdown": {"operation": "distribution", "note": "Use distribution for counts by category"},
    "distribution": {"operation": "distribution"},
    "correlation": {"operation": "correlation"},
    "compare": {"operation": "group_by", "note": "Use group_by + aggregate + sort. \"compare\" is an alias for group_by"},
    "versus": {"operation": "group_by", "note": "Use group_by + aggregate + sort"},
    "by": {"operation": "group_by", "note": "Use group_by + aggregate"},

    # KPI
    "kpi": {"operation": "kpi", "note": "Single value metric. Use aggregation"},
    "metric": {"operation": "kpi", "note": "Single value metric. Use aggregation"},

    # Forecast (NOT an operation — UI trigger)
    "forecast": {"operation": "time_series", "note": "FORECAST IS NOT AN OPERATION. Use time_series. The UI will show a forecast button after execution."},
    "predict": {"operation": "time_series", "note": "FORECAST IS NOT AN OPERATION. Use time_series. The UI will show a forecast button after execution."},
    "projection": {"operation": "time_series", "note": "FORECAST IS NOT AN OPERATION. Use time_series. The UI will show a forecast button after execution."},

    # Rolling / moving (NOT supported)
    "rolling": {"operation": "time_series", "note": "ROLLING AVERAGE IS NOT SUPPORTED. Use time_series for monthly totals."},
    "moving average": {"operation": "time_series", "note": "MOVING AVERAGE IS NOT SUPPORTED. Use time_series for monthly totals."},
    "growth": {"operation": "aggregate", "note": "GROWTH CALCULATION IS NOT SUPPORTED. Use aggregate for current totals."},
    "percentage change": {"operation": "aggregate", "note": "PERCENTAGE CHANGE IS NOT SUPPORTED. Use aggregate for current totals."},

    # Operators expressed as natural language (users say these, but they are NOT valid operators)
    "in": {"operation": "filter", "note": "Use multiple '=' filters or 'contains'. 'in' is NOT a supported operator."},
    "between": {"operation": "filter", "note": "Use two filters with >= and <=. 'between' is NOT a supported operator."},
    "last year": {"operation": "filter", "note": "Compute year-1 and use year_equals. 'last_year' is NOT a supported operator."},
    "this year": {"operation": "filter", "note": "Use current year with year_equals."},
    "within": {"operation": "filter", "note": "Use >= and <= filters. 'within' is NOT a supported operator."},
}

# =============================================================================
# PLAN TEMPLATES — common business questions → valid step sequences
# =============================================================================

PLAN_TEMPLATES = [
    {
        "name": "Top N by Metric",
        "description": "Find the top N items by a numeric metric",
        "when_to_use": "User asks for 'top 10 products', 'best customers', 'highest sales'",
        "steps": [
            {"operation": "group_by", "column": "<dimension_column>"},
            {"operation": "aggregate", "metric": "<numeric_column>", "aggregation": "sum"},
            {"operation": "sort", "column": "<numeric_column>", "order": "descending"},
            {"operation": "limit", "n": 10},
        ],
        "visualization": {"chart_type": "bar", "x_axis": "<dimension_column>", "y_axis": "<numeric_column>"},
    },
    {
        "name": "Bottom N by Metric",
        "description": "Find the bottom N items by a numeric metric",
        "when_to_use": "User asks for 'worst products', 'lowest sales', 'bottom 5 regions'",
        "steps": [
            {"operation": "group_by", "column": "<dimension_column>"},
            {"operation": "aggregate", "metric": "<numeric_column>", "aggregation": "sum"},
            {"operation": "sort", "column": "<numeric_column>", "order": "ascending"},
            {"operation": "limit", "n": 10},
        ],
        "visualization": {"chart_type": "bar", "x_axis": "<dimension_column>", "y_axis": "<numeric_column>"},
    },
    {
        "name": "Filter then Analyze",
        "description": "Apply a filter, then group and aggregate",
        "when_to_use": "User asks for 'sales in 2023', 'West region profit', 'Q1 orders'",
        "steps": [
            {"operation": "filter", "column": "<filter_column>", "operator": "=", "value": "<filter_value>"},
            {"operation": "group_by", "column": "<dimension_column>"},
            {"operation": "aggregate", "metric": "<numeric_column>", "aggregation": "sum"},
            {"operation": "sort", "column": "<numeric_column>", "order": "descending"},
        ],
        "visualization": {"chart_type": "bar", "x_axis": "<dimension_column>", "y_axis": "<numeric_column>"},
    },
    {
        "name": "Time Series",
        "description": "Show trend over time",
        "when_to_use": "User asks for 'monthly sales', 'sales trend', 'over time'",
        "steps": [
            {"operation": "time_series", "column": "<date_column>", "metric": "<numeric_column>"},
        ],
        "visualization": {"chart_type": "line", "x_axis": "<date_column>", "y_axis": "<numeric_column>"},
        "note": "time_series ALWAYS groups by MONTH and ALWAYS sums the metric. Do NOT add group_by or aggregate steps.",
    },
    {
        "name": "KPI Single Value",
        "description": "Return a single aggregated value",
        "when_to_use": "User asks for 'total sales', 'average profit', 'how many orders'",
        "steps": [
            {"operation": "kpi", "metric": "<numeric_column>", "aggregation": "sum"},
        ],
        "visualization": {"chart_type": "table"},
    },
    {
        "name": "Distribution",
        "description": "Count occurrences by category",
        "when_to_use": "User asks for 'distribution of categories', 'breakdown by region'",
        "steps": [
            {"operation": "distribution", "column": "<categorical_column>"},
        ],
        "visualization": {"chart_type": "pie", "x_axis": "<categorical_column>", "y_axis": "count"},
    },
    {
        "name": "Correlation",
        "description": "Correlation matrix of all numeric columns",
        "when_to_use": "User asks for 'correlation', 'relationship between sales and profit'",
        "steps": [
            {"operation": "correlation"},
        ],
        "visualization": {"chart_type": "table"},
    },
    {
        "name": "Comparison",
        "description": "Compare values across categories",
        "when_to_use": "User asks for 'compare regions', 'sales versus profit by category'",
        "steps": [
            {"operation": "group_by", "column": "<dimension_column>"},
            {"operation": "aggregate", "metric": "<numeric_column>", "aggregation": "sum"},
            {"operation": "sort", "column": "<numeric_column>", "order": "descending"},
        ],
        "visualization": {"chart_type": "bar", "x_axis": "<dimension_column>", "y_axis": "<numeric_column>"},
        "note": "\"compare\" is an alias for group_by. It does NOT perform actual comparison logic.",
    },
    {
        "name": "Date Filter + Analysis",
        "description": "Filter by year or month, then analyze",
        "when_to_use": "User asks for 'sales in 2023', 'January orders', 'last year'",
        "steps": [
            {"operation": "filter", "column": "<date_column>", "operator": "year_equals", "value": 2023},
            {"operation": "group_by", "column": "<dimension_column>"},
            {"operation": "aggregate", "metric": "<numeric_column>", "aggregation": "sum"},
        ],
        "visualization": {"chart_type": "bar", "x_axis": "<dimension_column>", "y_axis": "<numeric_column>"},
        "note": "For \"last year\", compute current year - 1. For \"this year\", use current year. Use year_equals, NOT a custom operator.",
    },
    {
        "name": "Multi-Filter",
        "description": "Apply multiple filters before analysis",
        "when_to_use": "User asks for 'sales in West region for 2023'",
        "steps": [
            {"operation": "filter", "column": "<date_column>", "operator": "year_equals", "value": 2023},
            {"operation": "filter", "column": "<region_column>", "operator": "=", "value": "West"},
            {"operation": "group_by", "column": "<dimension_column>"},
            {"operation": "aggregate", "metric": "<numeric_column>", "aggregation": "sum"},
        ],
        "visualization": {"chart_type": "bar", "x_axis": "<dimension_column>", "y_axis": "<numeric_column>"},
    },
]

# =============================================================================
# NEGATIVE EXAMPLES — what the LLM must NEVER generate
# =============================================================================

NEGATIVE_EXAMPLES = [
    {
        "user_question": "Forecast next 3 months",
        "invalid_plan": {"operation": "forecast", "column": "Order Date", "metric": "Sales"},
        "reason": "\"forecast\" is NOT a supported operation. It does not exist in SUPPORTED_OPERATIONS.",
        "correct_plan": [
            {"operation": "time_series", "column": "Order Date", "metric": "Sales"},
        ],
        "explanation": "Use time_series to show historical monthly data. The UI will display a forecast button after execution.",
    },
    {
        "user_question": "Sales in [2023, 2024]",
        "invalid_plan": {"operation": "filter", "column": "Order Date", "operator": "in", "value": [2023, 2024]},
        "reason": "\"in\" is NOT a supported filter operator. It does not exist in SUPPORTED_FILTER_OPERATORS.",
        "correct_plan": [
            {"operation": "filter", "column": "Order Date", "operator": "year_equals", "value": 2023},
        ],
        "explanation": "Use year_equals for a single year. For multiple years, add multiple filter steps.",
    },
    {
        "user_question": "Sales between 1000 and 5000",
        "invalid_plan": {"operation": "filter", "column": "Sales", "operator": "between", "value": [1000, 5000]},
        "reason": "\"between\" is NOT a supported filter operator. It does not exist in SUPPORTED_FILTER_OPERATORS.",
        "correct_plan": [
            {"operation": "filter", "column": "Sales", "operator": ">=", "value": 1000},
            {"operation": "filter", "column": "Sales", "operator": "<=", "value": 5000},
        ],
        "explanation": "Use two separate filter steps with >= and <=. \"between\" is not supported.",
    },
    {
        "user_question": "Sales last year",
        "invalid_plan": {"operation": "filter", "column": "Order Date", "operator": "last_year"},
        "reason": "\"last_year\" is NOT a supported filter operator. It does not exist in SUPPORTED_FILTER_OPERATORS.",
        "correct_plan": [
            {"operation": "filter", "column": "Order Date", "operator": "year_equals", "value": 2023},
        ],
        "explanation": "Compute the year value (current_year - 1) and use year_equals. Never invent custom operators.",
    },
    {
        "user_question": "Rolling average of sales",
        "invalid_plan": {"operation": "rolling_average", "column": "Order Date", "metric": "Sales"},
        "reason": "\"rolling_average\" is NOT a supported operation. It does not exist in SUPPORTED_OPERATIONS.",
        "correct_plan": [
            {"operation": "time_series", "column": "Order Date", "metric": "Sales"},
        ],
        "explanation": "Use time_series for monthly totals. Rolling average is not yet supported.",
    },
    {
        "user_question": "Growth by region",
        "invalid_plan": {"operation": "growth", "column": "Region", "metric": "Sales"},
        "reason": "\"growth\" is NOT a supported operation. It does not exist in SUPPORTED_OPERATIONS.",
        "correct_plan": [
            {"operation": "group_by", "column": "Region"},
            {"operation": "aggregate", "metric": "Sales", "aggregation": "sum"},
            {"operation": "sort", "column": "Sales", "order": "descending"},
        ],
        "explanation": "Use group_by + aggregate + sort. Growth calculation is not yet supported.",
    },
    {
        "user_question": "Percentage change in sales",
        "invalid_plan": {"operation": "percentage_change", "column": "Order Date", "metric": "Sales"},
        "reason": "\"percentage_change\" is NOT a supported operation. It does not exist in SUPPORTED_OPERATIONS.",
        "correct_plan": [
            {"operation": "time_series", "column": "Order Date", "metric": "Sales"},
        ],
        "explanation": "Use time_series for monthly totals. Percentage change is not yet supported.",
    },
    {
        "user_question": "Top 5 products by sales",
        "invalid_plan": [
            {"operation": "top_n", "n": 5},
        ],
        "reason": "\"top_n\" alone is incomplete. It is an alias for limit and requires group_by + aggregate + sort before it.",
        "correct_plan": [
            {"operation": "group_by", "column": "Product Name"},
            {"operation": "aggregate", "metric": "Sales", "aggregation": "sum"},
            {"operation": "sort", "column": "Sales", "order": "descending"},
            {"operation": "limit", "n": 5},
        ],
        "explanation": "top_n is just an alias for limit. You MUST group_by and aggregate first, then sort, then limit.",
    },
    {
        "user_question": "Compare regions",
        "invalid_plan": [
            {"operation": "compare", "column": "Region"},
        ],
        "reason": "\"compare\" is just an alias for group_by. It does NOT perform comparison logic.",
        "correct_plan": [
            {"operation": "group_by", "column": "Region"},
            {"operation": "aggregate", "metric": "Sales", "aggregation": "sum"},
            {"operation": "sort", "column": "Sales", "order": "descending"},
        ],
        "explanation": "compare is an alias for group_by. Always follow with aggregate and sort to produce meaningful comparison.",
    },
    {
        "user_question": "Time series with group_by",
        "invalid_plan": [
            {"operation": "group_by", "column": "Region"},
            {"operation": "time_series", "column": "Order Date", "metric": "Sales"},
            {"operation": "aggregate", "metric": "Sales", "aggregation": "sum"},
        ],
        "reason": "time_series ALREADY groups by month and sums the metric. Adding group_by or aggregate causes double-grouping.",
        "correct_plan": [
            {"operation": "time_series", "column": "Order Date", "metric": "Sales"},
        ],
        "explanation": "time_series is a self-contained operation. Do NOT add group_by or aggregate steps with it.",
    },
]

# =============================================================================
# CHART SELECTION GUIDANCE — which chart for which data shape
# =============================================================================

CHART_SELECTION_GUIDE = {
    "bar": {
        "when_to_use": "Categorical x-axis + numeric y-axis. Most common chart.",
        "requires": "1 categorical column (x_axis) + 1 numeric column (y_axis)",
        "examples": ["Sales by Region", "Top 10 Products", "Profit by Category"],
    },
    "line": {
        "when_to_use": "Time series data. Shows trend over time.",
        "requires": "Date column (x_axis) + numeric column (y_axis)",
        "examples": ["Monthly Sales Trend", "Profit Over Time"],
    },
    "pie": {
        "when_to_use": "Parts of a whole. Few categories (<= 8).",
        "requires": "1 categorical column + 1 numeric column (values)",
        "examples": ["Sales Distribution by Category", "Market Share"],
        "warning": "Do NOT use pie for many categories. Use bar instead.",
    },
    "scatter": {
        "when_to_use": "Relationship between two numeric variables.",
        "requires": "2 numeric columns (x_axis and y_axis)",
        "examples": ["Sales vs Profit", "Discount vs Profit Margin"],
    },
    "histogram": {
        "when_to_use": "Distribution of a single numeric variable.",
        "requires": "1 numeric column (x_axis)",
        "examples": ["Sales Distribution", "Order Value Distribution"],
    },
    "box": {
        "when_to_use": "Distribution of numeric by category.",
        "requires": "1 categorical column (optional) + 1 numeric column (y_axis)",
        "examples": ["Profit Distribution by Region", "Sales by Category"],
    },
    "table": {
        "when_to_use": "Fallback for any unsupported chart type. Also for KPI and correlation.",
        "requires": "Any data shape",
        "examples": ["KPI Value", "Correlation Matrix", "Raw Data"],
        "note": "Always safe to use table. Use it when unsure.",
    },
}

# =============================================================================
# DATE HANDLING RULES — how to translate date concepts into valid filters
# =============================================================================

DATE_HANDLING_RULES = """
Date Filtering Rules:

1. ONLY these date operators exist: year_equals, month_equals
   There is NO "last_year", "this_year", "between", "in", "range" operator.

2. "Last year" → compute (current_year - 1), then use year_equals
   Example: {"operation": "filter", "column": "Order Date", "operator": "year_equals", "value": 2023}

3. "This year" → use current year with year_equals
   Example: {"operation": "filter", "column": "Order Date", "operator": "year_equals", "value": 2024}

4. "Q1 2024" → filter year_equals 2024, then the result is already monthly
   Do NOT try to filter by quarter. The engine does not support quarter filtering.

5. "January" → month_equals 1
   Example: {"operation": "filter", "column": "Order Date", "operator": "month_equals", "value": 1}

6. Date range (e.g., "between Jan 2023 and Dec 2023"):
   Use TWO separate filter steps:
   {"operation": "filter", "column": "Order Date", "operator": "year_equals", "value": 2023}
   Do NOT use a "between" operator. It does not exist.

7. time_series operation:
   - ALWAYS groups by MONTH automatically
   - ALWAYS sums the metric automatically
   - Requires: date column + metric column
   - Do NOT add group_by or aggregate with time_series
   - Output format: YYYY-MM strings

8. The DataCleaner auto-parses columns containing "date" in their name.
   If a date column is not detected, it may be named differently.
   Use ONLY the column names from the dataset schema.
"""