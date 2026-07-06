import logging
from core.ai_client import AIClient
from models.analysis_result import AnalysisResult

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Senior Business Intelligence Analyst presenting findings to an executive audience.

Your task is to explain data analysis results in a professional, concise, and presentation-ready format.

STRICT RULES:
- Use ONLY values present in the provided data. Never invent numbers, percentages, or trends.
- If the data does not support a conclusion, explicitly state that.
- Write in professional business language. No emojis. No technical jargon (Python, Pandas, DataFrame, etc.).
- Be direct and insightful. Avoid generic phrases like "Sales are high" or "The data shows interesting patterns."
- Maximum length: approximately 200-250 words total.
- Always use the exact 4-section format below with ## headers.

OUTPUT FORMAT:

## Executive Summary
2-3 concise sentences summarizing the key finding. Mention the most important number.

## Key Insights
- 3-5 bullet points using actual values from the data
- Each bullet should cite a specific number or fact
- Order by importance (most significant first)

## Business Interpretation
Explain what these results imply for the business, based ONLY on the available data. Do not speculate about causes or external factors. If implications are limited, say so directly.

## Recommended Actions
Provide 2-3 practical, data-driven recommendations. Each must be directly supported by the analysis results. If the data is insufficient for recommendations, state that clearly.
"""


class ExplanationEngine:

    def __init__(self):
        self.client = AIClient()

    def explain(self, result: AnalysisResult) -> str:
        if not result.success:
            return f"Analysis could not be completed: {result.error}"

        if not result.data:
            return (
                "## Executive Summary\n"
                "The analysis completed but returned no data rows.\n\n"
                "## Key Insights\n"
                "- No data available to extract insights from.\n\n"
                "## Business Interpretation\n"
                "Without data, no business interpretation can be provided.\n\n"
                "## Recommended Actions\n"
                "Consider rephrasing your question or checking the dataset for the requested information."
            )

        try:
            user_prompt = self._build_user_prompt(result)
            explanation = self.client.ask(SYSTEM_PROMPT, user_prompt)
            return self._minimal_cleanup(explanation)

        except Exception as e:
            logger.exception("ExplanationEngine failed")
            return (
                "## Executive Summary\n"
                "Analysis completed successfully, but the insight generation encountered an issue.\n\n"
                "## Key Insights\n"
                f"- The analysis returned {result.row_count} rows of data.\n"
                "- Please review the chart and data table for the detailed results.\n\n"
                "## Business Interpretation\n"
                "The data is available in the table above for manual review.\n\n"
                "## Recommended Actions\n"
                "Review the visualization and data table to draw your own conclusions."
            )

    def _build_user_prompt(self, result: AnalysisResult) -> str:
        data_preview = result.data[:20]  # Limit to first 20 rows for token efficiency

        prompt = f"""Business Question: {result.question or "Unspecified question"}

Analysis Results:
- Rows returned: {result.row_count}
- Columns: {', '.join(result.columns or [])}

Data (first {len(data_preview)} rows):
{data_preview}

Provide your explanation in the exact 4-section format specified in your instructions."""

        return prompt

    def _minimal_cleanup(self, text: str) -> str:
        # Strip leading/trailing whitespace
        text = text.strip()
        # Remove markdown code fences if the LLM wrapped output in them
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        return text