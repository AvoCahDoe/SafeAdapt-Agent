"""Goal specification schemas."""

from pydantic import BaseModel, ConfigDict, Field


class GoalSpecification(BaseModel):
    """Immutable agent goal and safety constraints.

    The original specification must never be silently modified by agent memory.
    """

    model_config = ConfigDict(frozen=True)

    primary_goal: str
    safety_constraints: list[str] = Field(default_factory=list)
    user_preferences: list[str] = Field(default_factory=list)
    forbidden_actions: list[str] = Field(default_factory=list)
    approval_required_actions: list[str] = Field(default_factory=list)

    def snapshot(self) -> "GoalSpecification":
        """Return an immutable copy of this goal specification."""
        return self.model_copy(deep=True)
