from typing import Any
from pydantic import BaseModel


class DatasetProfile(BaseModel):
    rows: int
    columns: int
    column_names: list[str]
    data_types: dict[str, str]
    numeric_columns: list[str]
    categorical_columns: list[str]
    date_columns: list[str]
    missing_values: dict[str, int]
    sample_data: list[dict[str, Any]]