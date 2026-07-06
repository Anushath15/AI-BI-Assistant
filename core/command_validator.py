import json
import logging
from typing import Optional
from pydantic import ValidationError

from models.execution_plan import ExecutionPlan
from models.dataset_profile import DatasetProfile
from utils.logger import get_logger

logger = get_logger(__name__)

# Keywords that indicate a strategic/consulting question
# that cannot map to a single execution plan
STRATEGIC_KEYWORDS = [
    "business problems", "strategic", "consulting", "recommend",
    "advise", "strategy", "opportunities", "weaknesses", "strengths",
    "imagine you are", "act as", "pretend", "role play",
    "biggest challenges", "executive summary", "board report",
]

PROFESSIONAL_NARROWING_MESSAGE = (
    "This question covers multiple analyses at once. "
    "For best results, ask one specific question at a time. "
    "For example:\n"
    "• 'Which category has the lowest profit?'\n"
    "• 'Show me the sales trend for 2023'\n"
    "• 'Which region is underperforming?'\n"
    "• 'What are the top 5 products by revenue?'"
)


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
        original_question: str = "",
    ) -> ValidationResult:

        # Step 1: Check if question is too broad for single plan
        if self._is_strategic_question(original_question):
            logger.info("Question classified as strategic — returning narrowing message")
            return ValidationResult(
                success=False,
                error=PROFESSIONAL_NARROWING_MESSAGE,
            )

        # Step 2: Clean markdown fences
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1]).strip()

        # Step 3: Extract first JSON object if extra text exists
        cleaned = self._extract_first_json(cleaned)

        # Step 4: Parse JSON
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.warning("JSON parse failed: %s", e)
            return ValidationResult(
                success=False,
                error=(
                    "The AI returned an unstructured response for this question. "
                    "Please try rephrasing as a specific analytical question, such as:\n"
                    "• 'Which product had the highest sales?'\n"
                    "• 'Show profit by region'\n"
                    "• 'What was the sales trend in 2023?'"
                ),
            )

        # Step 5: Validate structure with Pydantic
        try:
            plan = ExecutionPlan.model_validate(data)
        except ValidationError as e:
            errors = e.errors()
            msg = errors[0]["msg"] if errors else str(e)
            return ValidationResult(
                success=False,
                error=f"Invalid execution plan structure: {msg}",
            )

        # Step 6: Validate column names against actual dataset
        valid_columns = set(profile.column_names)
        numeric_columns = set(profile.numeric_columns)

        for i, step in enumerate(plan.steps):
            if step.column and step.column not in valid_columns:
                return ValidationResult(
                    success=False,
                    error=(
                        f"Column '{step.column}' not found in dataset. "
                        f"Available columns: {sorted(valid_columns)}"
                    ),
                )

            if step.metric and step.metric not in valid_columns:
                return ValidationResult(
                    success=False,
                    error=(
                        f"Metric '{step.metric}' not found in dataset. "
                        f"Available columns: {sorted(valid_columns)}"
                    ),
                )

            if step.metric and step.metric not in numeric_columns:
                return ValidationResult(
                    success=False,
                    error=(
                        f"'{step.metric}' is not a numeric column. "
                        f"Numeric columns: {sorted(numeric_columns)}"
                    ),
                )

        logger.info(
            "ExecutionPlan validated: %d steps, chart=%s",
            len(plan.steps),
            plan.visualization.chart_type,
        )
        return ValidationResult(success=True, plan=plan)

    def _is_strategic_question(self, question: str) -> bool:
        if not question:
            return False
        q_lower = question.lower()
        return any(kw in q_lower for kw in STRATEGIC_KEYWORDS)

    def _extract_first_json(self, text: str) -> str:
        """
        Extract the first complete JSON object from text.
        Handles cases where the LLM adds explanation after the JSON.
        """
        start = text.find("{")
        if start == -1:
            return text

        depth = 0
        for i, char in enumerate(text[start:], start):
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]

        return text[start:]