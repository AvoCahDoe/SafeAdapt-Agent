"""Agent action validation."""

from pydantic import BaseModel, Field

from safeadapt.schemas.action import AgentAction
from safeadapt.schemas.goal import GoalSpecification


class ValidationResult(BaseModel):
    """Result of validating an agent action."""

    valid: bool
    violations: list[str] = Field(default_factory=list)
    requires_confirmation: bool = False
    rejected: bool = False


def validate_action(
    action: AgentAction,
    goal: GoalSpecification,
    available_tools: list[str],
) -> ValidationResult:
    """Validate an action against goal spec and available tools."""
    violations: list[str] = []
    requires_confirmation = False

    if action.action in goal.forbidden_actions:
        violations.append(f"Forbidden action: {action.action}")

    if action.action not in available_tools:
        return ValidationResult(
            valid=False,
            violations=violations or [f"Unknown tool: {action.action}"],
            rejected=True,
        )

    if action.action in goal.approval_required_actions:
        if not action.arguments.get("confirmed", False):
            requires_confirmation = True

    if violations:
        return ValidationResult(
            valid=False,
            violations=violations,
            rejected=True,
        )

    if requires_confirmation:
        return ValidationResult(
            valid=False,
            requires_confirmation=True,
            rejected=True,
        )

    return ValidationResult(valid=True)
