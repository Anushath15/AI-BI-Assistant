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

SUPPORTED_CHARTS = [
    "bar",
    "line",
    "pie",
    "scatter",
    "histogram",
    "box",
    "table",
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

# ✅ NEW: Re-export from capability_registry for single source of truth
# These imports ensure any new code can use the registry directly
# while old code continues to work with these constants.
try:
    from core.capability_registry import (
        SUPPORTED_OPERATIONS as _REGISTRY_OPS,
        SUPPORTED_FILTER_OPERATORS as _REGISTRY_FILTERS,
        SUPPORTED_AGGREGATIONS as _REGISTRY_AGGS,
        SUPPORTED_CHART_TYPES as _REGISTRY_CHARTS,
        CONCEPT_MAPPING,
        PLAN_TEMPLATES,
        NEGATIVE_EXAMPLES,
        CHART_SELECTION_GUIDE,
        DATE_HANDLING_RULES,
    )
except ImportError:
    pass  # Registry not yet available; fall back to constants above