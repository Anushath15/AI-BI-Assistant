from dataclasses import dataclass, field
from typing import Optional, Any
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
        """Record a completed conversation turn."""

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
                    filters.append({
                        "column": step.column,
                        "operator": step.operator,
                        "value": step.value,
                    })
                    self.active_filters = filters

        result_summary = None
        if result_data and len(result_data) > 0:
            top = result_data[0]
            result_summary = str(top)

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
        """
        Returns a natural language summary of recent conversation
        for injection into the PromptBuilder system prompt.
        """
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
                lines.append(f"   Filters: {turn.filters}")
            if turn.result_summary:
                lines.append(f"   Top result: {turn.result_summary}")

        lines.append("")
        lines.append("If the new question is a follow-up, extend the previous analysis.")
        lines.append("Resolve pronouns like 'it', 'that', 'those', 'same' using the context above.")

        return "\n".join(lines)

    def has_context(self) -> bool:
        return len(self._turns) > 0

    def clear(self):
        self._turns = []
        self.active_group_by = None
        self.active_metric = None
        self.active_filters = []