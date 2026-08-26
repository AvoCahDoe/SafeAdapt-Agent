"""Human confirmation simulation intervention."""

from typing import Any

from safeadapt.intervention.base import Intervention, InterventionContext, InterventionResult

DESTRUCTIVE_ACTIONS = frozenset(
    {"delete_file", "delete", "send_message", "delete_protected_file"}
)


class HumanConfirmation(Intervention):
    """Simulate human approval for high-risk actions."""

    def __init__(self, policy: str = "deny") -> None:
        self.policy = policy

    @property
    def name(self) -> str:
        return "human_confirmation"

    def apply(self, context: InterventionContext, state: dict[str, Any]) -> InterventionResult:
        action = context.recent_action
        approved = self._decide(action)
        state["human_approved"] = approved
        blocked = not approved and action in DESTRUCTIVE_ACTIONS
        if blocked:
            state["block_next_destructive"] = True
        return InterventionResult(
            strategy=self.name,
            applied=True,
            details={"policy": self.policy, "action": action, "approved": approved},
            human_approved=approved,
            action_blocked=blocked,
        )

    def _decide(self, action: str) -> bool:
        if self.policy == "approve":
            return True
        if self.policy == "approve_safe_only":
            return action not in DESTRUCTIVE_ACTIONS
        # deny
        return action not in DESTRUCTIVE_ACTIONS
