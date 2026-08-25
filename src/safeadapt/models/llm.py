"""LLM provider abstract interface."""

from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    """Abstract LLM provider for agent action generation."""

    @abstractmethod
    async def generate(self, prompt: str, context: dict[str, Any]) -> dict[str, Any]:
        """Generate a structured action from prompt and context."""
