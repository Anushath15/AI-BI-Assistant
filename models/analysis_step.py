from typing import Any, Optional
from pydantic import BaseModel, field_validator

from utils.constants import (
    SUPPORTED_OPERATIONS,
    SUPPORTED_AGGREGATIONS,
    SUPPORTED_FILTER_OPERATORS,
)


class AnalysisStep(BaseModel):

    operation: str
    column: Optional[str] = None
    metric: Optional[str] = None
    aggregation: Optional[str] = None
    operator: Optional[str] = None
    value: Optional[Any] = None
    order: Optional[str] = None
    n: Optional[int] = None

    @field_validator("operation")
    @classmethod
    def operation_must_be_supported(cls, v):
        if v not in SUPPORTED_OPERATIONS:
            raise ValueError(
                f"Unsupported operation '{v}'. "
                f"Allowed: {SUPPORTED_OPERATIONS}"
            )
        return v

    @field_validator("aggregation")
    @classmethod
    def aggregation_must_be_supported(cls, v):
        if v is not None and v not in SUPPORTED_AGGREGATIONS:
            raise ValueError(
                f"Unsupported aggregation '{v}'. "
                f"Allowed: {SUPPORTED_AGGREGATIONS}"
            )
        return v

    @field_validator("operator")
    @classmethod
    def operator_must_be_supported(cls, v):
        if v is not None and v not in SUPPORTED_FILTER_OPERATORS:
            raise ValueError(
                f"Unsupported filter operator '{v}'. "
                f"Allowed: {SUPPORTED_FILTER_OPERATORS}"
            )
        return v

    @field_validator("order")
    @classmethod
    def order_must_be_valid(cls, v):
        if v is not None and v not in ("ascending", "descending"):
            raise ValueError("order must be 'ascending' or 'descending'")
        return v