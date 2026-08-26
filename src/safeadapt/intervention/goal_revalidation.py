"""Goal revalidation intervention."""

from typing import Any

from safeadapt.intervention.base import Intervention, InterventionContext, InterventionResult


class GoalRevalidation(Intervention):
    """Reinject the original immutable goal and force re-evaluation."""

    @property
    def name(self) -> str:
        return "goal_revalidation"

    def apply(self, context: InterventionContext, state: dict[str, Any]) -> InterventionResult:
        state["revalidate_goal"] = True
        goal = state.get("goal")
        details = {
            "message": "Original goal and safety constraints reinjected",
            "primary_goal": getattr(goal, "primary_goal", None),
            "constraints": list(getattr(goal, "safety_constraints", [])),
        }
        return InterventionResult(
            strategy=self.name,
            applied=True,
            details=details,
            revalidate_goal=True,
        )
