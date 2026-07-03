from typing import Optional
from pydantic import BaseModel, field_validator

from models.analysis_step import AnalysisStep
from utils.constants import SUPPORTED_CHARTS


class VisualizationConfig(BaseModel):
    chart_type: str
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    title: Optional[str] = None

    @field_validator("chart_type")
    @classmethod
    def chart_must_be_supported(cls, v):
        if v not in SUPPORTED_CHARTS:
            raise ValueError(
                f"Unsupported chart '{v}'. "
                f"Allowed: {SUPPORTED_CHARTS}"
            )
        return v


class ExecutionPlan(BaseModel):
    steps: list[AnalysisStep]
    visualization: VisualizationConfig
    question: Optional[str] = None

    @field_validator("steps")
    @classmethod
    def steps_must_not_be_empty(cls, v):
        if not v:
            raise ValueError("ExecutionPlan must contain at least one step.")
        return v