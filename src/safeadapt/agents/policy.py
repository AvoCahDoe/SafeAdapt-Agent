"""Agent policy and context building."""

from typing import Any

from safeadapt.schemas.goal import GoalSpecification
from safeadapt.schemas.memory import MemoryItem


class AgentPolicy:
    """Builds prompt context from goal, memory, task, and tools."""

    def build_context(
        self,
        goal: GoalSpecification,
        task: str,
        memory_items: list[MemoryItem],
        available_tools: list[str],
        observation: dict[str, Any],
        interaction_id: int = 0,
    ) -> dict[str, Any]:
        """Construct context dict for LLM generation."""
        return {
            "interaction_id": interaction_id,
            "goal": goal.primary_goal,
            "safety_constraints": list(goal.safety_constraints),
            "user_preferences": list(goal.user_preferences),
            "forbidden_actions": list(goal.forbidden_actions),
            "approval_required_actions": list(goal.approval_required_actions),
            "memory": [
                {"content": m.content, "type": m.type.value, "source": m.source}
                for m in memory_items
            ],
            "task": task,
            "available_tools": available_tools,
            "observation": observation,
        }

    def build_prompt(self, context: dict[str, Any]) -> str:
        """Build a text prompt from context (for future LLM providers)."""
        lines = [
            f"GOAL: {context['goal']}",
            "SAFETY CONSTRAINTS:",
            *[f"  - {c}" for c in context["safety_constraints"]],
            f"CURRENT TASK: {context['task']}",
            f"AVAILABLE TOOLS: {', '.join(context['available_tools'])}",
        ]
        if context["memory"]:
            lines.append("MEMORY:")
            for m in context["memory"]:
                lines.append(f"  - [{m['type']}] {m['content']}")
        return "\n".join(lines)
