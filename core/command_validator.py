import json
import logging
from typing import Optional
from pydantic import ValidationError

from models.execution_plan import ExecutionPlan
from models.dataset_profile import DatasetProfile

logger = logging.getLogger(__name__)


class ValidationResult:
    def __init__(
        self,
        success: bool,
        plan: Optional[ExecutionPlan] = None,
        error: Optional[str] = None,
    ):
        self.success = success
        self.plan = plan
        self.error = error

    def __iter__(self):
        if self.success:
            yield self.success
            yield self.plan
        else:
            yield self.success
            yield self.error


class CommandValidator:

    def validate(
        self,
        raw_response: str,
        profile: DatasetProfile,
    ) -> ValidationResult:

        # Step 1: Strip markdown fences if model added them
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1]).strip()

        # Step 2: Parse JSON
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            return ValidationResult(
                success=False,
                error=f"AI returned invalid JSON: {e}",
            )

        # Step 3: Validate structure with Pydantic
        try:
            plan = ExecutionPlan.model_validate(data)
        except ValidationError as e:
            errors = e.errors()
            msg = errors[0]["msg"] if errors else str(e)
            return ValidationResult(
                success=False,
                error=f"Invalid execution plan structure: {msg}",
            )

        # Step 4: Validate column names against actual dataset
        valid_columns = set(profile.column_names)
        numeric_columns = set(profile.numeric_columns)

        for i, step in enumerate(plan.steps):

            if step.column and step.column not in valid_columns:
                return ValidationResult(
                    success=False,
                    error=(
                        f"Step {i+1} references unknown column "
                        f"'{step.column}'. "
                        f"Available columns: {sorted(valid_columns)}"
                    ),
                )

            if step.metric and step.metric not in valid_columns:
                return ValidationResult(
                    success=False,
                    error=(
                        f"Step {i+1} references unknown metric "
                        f"'{step.metric}'. "
                        f"Available columns: {sorted(valid_columns)}"
                    ),
                )

            if step.metric and step.metric not in numeric_columns:
                return ValidationResult(
                    success=False,
                    error=(
                        f"Step {i+1} metric '{step.metric}' is not numeric. "
                        f"Numeric columns: {sorted(numeric_columns)}"
                    ),
                )

        logger.info(
            "ExecutionPlan validated: %d steps, chart=%s",
            len(plan.steps),
            plan.visualization.chart_type,
        )

        return ValidationResult(success=True, plan=plan)