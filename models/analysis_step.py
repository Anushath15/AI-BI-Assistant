from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class AnalysisStep:
    """
    Represents a single executable analysis step.

    Example:
        Filter rows
        Group by Category
        Aggregate Sales
        Sort descending
        Limit top 10
    """

    # Name of the operation
    operation: str

    # Column involved in the operation
    column: Optional[str] = None

    # Metric column (e.g., Sales, Profit)
    metric: Optional[str] = None

    # Aggregation method (sum, mean, count...)
    aggregation: Optional[str] = None

    # Filter operator (=, >, <, contains...)
    operator: Optional[str] = None

    # Filter value
    value: Optional[Any] = None

    # Sort order
    order: Optional[str] = None

    # Extra parameters for future extensions
    parameters: Optional[dict] = None