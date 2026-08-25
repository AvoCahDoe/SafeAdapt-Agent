"""Base environment interface."""

from abc import ABC, abstractmethod
from typing import Any

from safeadapt.schemas.action import AgentAction
from safeadapt.schemas.environment import ActionResult


class BaseEnvironment(ABC):
    """Abstract simulated environment for agent interaction."""

    @abstractmethod
    def observe(self) -> dict[str, Any]:
        """Return current environment observation."""

    @abstractmethod
    def execute(self, action: AgentAction) -> ActionResult:
        """Execute an agent action and return the result."""

    @abstractmethod
    def reset(self) -> None:
        """Reset environment to initial state."""

    @abstractmethod
    def get_available_tools(self) -> list[str]:
        """Return names of tools available in this environment."""
