"""
core/conversation_context.py

Responsibility: Maintain AI planning context within a session.

Tracks what the AI planned in previous turns so follow-up questions
like "which one performed worst?" and "now filter by 2023" work correctly.

Separate from SessionManager which handles UI rendering history.
This module is purely for AI prompt injection.
"""

from dataclasses import dataclass, field
from typing import Optional
from models.execution_plan import ExecutionPlan


@dataclass
class ConversationTurn:
    question: str
    execution_plan: Optional[dict] = None
    result_summary: Optional[str] = None
    group_by: Optional[str] = None
    metric: Optional[str] = None
    filters: list[dict] = field(default_factory=list)


class ConversationContext:

    MAX_TURNS = 5

    def __init__(self):
        self._turns: list[ConversationTurn] = []
        self.active_dataset: Optional[str] = None
        self.active_group_by: Optional[str] = None
        self.active_metric: Optional[str] = None
        self.active_filters: list[dict] = []

    def add_turn(
        self,
        question: str,
        plan: Optional[ExecutionPlan] = None,
        result_data: Optional[list] = None,
    ):
        group_by = None
        metric = None
        filters = []

        if plan:
            for step in plan.steps:
                if step.operation == "group_by":
                    group_by = step.column
                    self.active_group_by = step.column
                if step.operation == "aggregate":
                    metric = step.metric
                    self.active_metric = step.metric
                if step.operation == "filter":
                    filter_entry = {
                        "column": step.column,
                        "operator": step.operator,
                        "value": step.value,
                    }
                    filters.append(filter_entry)
                    existing = [
                        f for f in self.active_filters
                        if f.get("column") != step.column
                    ]
                    existing.append(filter_entry)
                    self.active_filters = existing

        result_summary = None
        if result_data and len(result_data) > 0:
            top = result_data[0]
            parts = [f"{k}: {v}" for k, v in top.items()]
            result_summary = ", ".join(parts)

        turn = ConversationTurn(
            question=question,
            execution_plan=plan.model_dump() if plan else None,
            result_summary=result_summary,
            group_by=group_by,
            metric=metric,
            filters=filters,
        )

        self._turns.append(turn)
        if len(self._turns) > self.MAX_TURNS:
            self._turns.pop(0)

    def get_context_summary(self) -> str:
        if not self._turns:
            return ""

        lines = ["Recent conversation context:"]
        for i, turn in enumerate(self._turns[-3:], 1):
            lines.append(f"{i}. User asked: {turn.question}")
            if turn.group_by:
                lines.append(f"   Grouped by: {turn.group_by}")
            if turn.metric:
                lines.append(f"   Metric: {turn.metric}")
            if turn.filters:
                lines.append(f"   Filters applied: {turn.filters}")
            if turn.result_summary:
                lines.append(f"   Top result: {turn.result_summary}")

        lines.append("")
        lines.append("If the new question is a follow-up, extend the previous analysis.")
        lines.append("Resolve pronouns like 'it', 'that', 'those', 'which one', 'same' from the context above.")

        return "\n".join(lines)

    def has_context(self) -> bool:
        return len(self._turns) > 0

    def clear(self):
        self._turns = []
        self.active_group_by = None
        self.active_metric = None
        self.active_filters = []