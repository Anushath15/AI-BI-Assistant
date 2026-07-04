import logging
from core.ai_client import AIClient
from models.analysis_result import AnalysisResult

logger = logging.getLogger(__name__)

EXPLANATION_SYSTEM_PROMPT = """You are a Business Intelligence Analyst.

You will receive the result of a data analysis and the original business question.

Your job is to explain the result in clear, concise business language.

Rules:
- Write 2 to 4 sentences maximum.
- Use business language, not technical language.
- Mention specific numbers and values from the result.
- Do not mention Python, Pandas, DataFrames, or any technical terms.
- Do not repeat the question back to the user.
- Be direct and insightful.
"""


class ExplanationEngine:

    def __init__(self):
        self.client = AIClient()

    def explain(self, result: AnalysisResult) -> str:

        if not result.success:
            return f"Analysis could not be completed: {result.error}"

        if not result.data:
            return "The analysis returned no data."

        try:
            user_prompt = f"""Business Question:
{result.question}

Analysis Result ({result.row_count} rows):
{result.data}

Provide a brief business explanation of these results."""

            explanation = self.client.ask(
                EXPLANATION_SYSTEM_PROMPT,
                user_prompt,
            )

            return explanation.strip().replace("`", "")

        except Exception as e:
            logger.exception("ExplanationEngine failed")
            return "Analysis completed successfully. Please review the chart and data above."