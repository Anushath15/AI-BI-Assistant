from typing import Optional
from pydantic import BaseModel


class BusinessSchema(BaseModel):
    dataset_name: str
    measures: list[str]
    dimensions: list[str]
    date_columns: list[str]
    kpi_columns: list[str]
    id_columns: list[str]
    semantic_labels: dict[str, str]
    aggregation_hints: dict[str, str]
    business_summary: str