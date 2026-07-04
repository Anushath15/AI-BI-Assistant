"""
core/session_manager.py

Responsibility: Manage conversation history for the chat interface.
Stores questions, results, and context across turns.
"""

from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class ChatEntry:
    question: str
    explanation: Optional[str] = None
    data: Optional[list] = None
    error: Optional[str] = None
    figure: Optional[Any] = None


class SessionManager:

    def __init__(self):
        self.history: list[ChatEntry] = []

    def add(self, entry: ChatEntry):
        self.history.append(entry)

    def get_history(self) -> list[ChatEntry]:
        return self.history

    def clear(self):
        self.history = []

    def last_question(self) -> Optional[str]:
        if self.history:
            return self.history[-1].question
        return None