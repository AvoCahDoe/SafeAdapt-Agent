"""Base agent model."""

from dataclasses import dataclass, field

from safeadapt.agents.memory import AgentMemory
from safeadapt.agents.policy import AgentPolicy
from safeadapt.schemas.experiment import MemoryMode
from safeadapt.schemas.goal import GoalSpecification


@dataclass
class Agent:
    """Research agent with immutable goal and optional persistent memory."""

    agent_id: str
    system_goal: GoalSpecification
    memory: AgentMemory
    policy: AgentPolicy = field(default_factory=AgentPolicy)
    available_tools: list[str] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        agent_id: str,
        goal: GoalSpecification,
        memory_mode: MemoryMode,
        tools: list[str],
    ) -> "Agent":
        """Factory to create an agent with the given configuration."""
        return cls(
            agent_id=agent_id,
            system_goal=goal.snapshot(),
            memory=AgentMemory(mode=memory_mode),
            available_tools=tools,
        )
