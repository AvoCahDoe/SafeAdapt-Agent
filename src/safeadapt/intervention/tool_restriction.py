"""Tool restriction intervention."""

from typing import Any

from safeadapt.intervention.base import Intervention, InterventionContext, InterventionResult

DEFAULT_DANGEROUS_TOOLS = frozenset(
    {"delete_file", "delete", "send_message", "delete_protected_file"}
)


class ToolRestriction(Intervention):
    """Temporarily disable dangerous tools."""

    def __init__(
        self,
        duration: int = 10,
        dangerous_tools: frozenset[str] | None = None,
    ) -> None:
        self.duration = duration
        self.dangerous_tools = dangerous_tools or DEFAULT_DANGEROUS_TOOLS

    @property
    def name(self) -> str:
        return "tool_restriction"

    def apply(self, context: InterventionContext, state: dict[str, Any]) -> InterventionResult:
        to_restrict = [
            t for t in context.available_tools if t in self.dangerous_tools
        ]
        existing = set(state.get("restricted_tools", []))
        existing.update(to_restrict)
        state["restricted_tools"] = list(existing)
        remaining = max(state.get("restriction_remaining", 0), self.duration)
        state["restriction_remaining"] = remaining
        return InterventionResult(
            strategy=self.name,
            applied=True,
            details={"restricted": to_restrict, "duration": remaining},
            restricted_tools=to_restrict,
            restriction_remaining=remaining,
        )
