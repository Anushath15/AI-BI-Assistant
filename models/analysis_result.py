from typing import Any, Optional
from pydantic import BaseModel


class AnalysisResult(BaseModel):
    success: bool
    question: Optional[str] = None
    data: Optional[list[dict[str, Any]]] = None
    row_count: Optional[int] = None
    columns: Optional[list[str]] = None
    error: Optional[str] = None
    execution_steps_run: Optional[int] = None

    model_config = {"arbitrary_types_allowed": True}

    @classmethod
    def from_failure(cls, error: str, question: str = None) -> "AnalysisResult":
        return cls(success=False, error=error, question=question)