"""Base intervention interface."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class InterventionContext(BaseModel):
    """Context passed to interventions when drift is detected."""

    interaction_id: int
    severity: str
    drift_score: float
    recent_action: str = ""
    recent_arguments: dict[str, Any] = Field(default_factory=dict)
    violations: list[str] = Field(default_factory=list)
    available_tools: list[str] = Field(default_factory=list)


class InterventionResult(BaseModel):
    """Outcome of applying an intervention."""

    strategy: str
    applied: bool = True
    details: dict[str, Any] = Field(default_factory=dict)
    restricted_tools: list[str] = Field(default_factory=list)
    restriction_remaining: int = 0
    revalidate_goal: bool = False
    memory_rolled_back: bool = False
    human_approved: bool | None = None
    action_blocked: bool = False


class Intervention(ABC):
    """Abstract intervention strategy."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy name matching InterventionStrategy enum values."""

    @abstractmethod
    def apply(self, context: InterventionContext, state: dict[str, Any]) -> InterventionResult:
        """Apply the intervention given context and mutable runner state."""
