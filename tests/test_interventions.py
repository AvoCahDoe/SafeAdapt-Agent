"""Tests for intervention strategies and manager."""

from safeadapt.agents.memory import AgentMemory
from safeadapt.intervention.base import InterventionContext
from safeadapt.intervention.goal_revalidation import GoalRevalidation
from safeadapt.intervention.human_confirmation import HumanConfirmation
from safeadapt.intervention.manager import InterventionManager
from safeadapt.intervention.memory_rollback import MemoryRollback
from safeadapt.intervention.tool_restriction import ToolRestriction
from safeadapt.schemas.drift import DriftScore, DriftSeverity
from safeadapt.schemas.experiment import InterventionSection, InterventionStrategy, MemoryMode
from safeadapt.schemas.goal import GoalSpecification
from safeadapt.schemas.memory import MemoryType


def _ctx(**kwargs) -> InterventionContext:
    defaults = {
        "interaction_id": 10,
        "severity": "high",
        "drift_score": 0.5,
        "recent_action": "delete_file",
        "available_tools": ["list_files", "read_file", "delete_file", "send_message"],
        "violations": ["Cannot delete protected file"],
    }
    defaults.update(kwargs)
    return InterventionContext(**defaults)


class TestGoalRevalidation:
    def test_sets_revalidate_flag(self) -> None:
        goal = GoalSpecification(primary_goal="Organize files", safety_constraints=["Be safe"])
        state = {"goal": goal}
        result = GoalRevalidation().apply(_ctx(), state)
        assert result.revalidate_goal
        assert state["revalidate_goal"] is True


class TestToolRestriction:
    def test_restricts_dangerous_tools(self) -> None:
        state: dict = {}
        result = ToolRestriction(duration=5).apply(_ctx(), state)
        assert "delete_file" in result.restricted_tools
        assert "send_message" in result.restricted_tools
        assert state["restriction_remaining"] == 5


class TestMemoryRollback:
    def test_rollback_without_snapshot(self) -> None:
        mem = AgentMemory(mode=MemoryMode.PERSISTENT)
        for i in range(5):
            mem.add(f"item-{i}", "test", MemoryType.PAST_ACTION, timestamp=i)
        state = {"memory": mem}
        result = MemoryRollback(rollback_n=2).apply(_ctx(), state)
        assert result.memory_rolled_back
        assert len(mem.retrieve()) == 3

    def test_restore_snapshot(self) -> None:
        mem = AgentMemory(mode=MemoryMode.PERSISTENT)
        mem.add("a", "test", MemoryType.PAST_ACTION)
        mem.snapshot()
        mem.add("b", "test", MemoryType.PAST_ACTION)
        state = {"memory": mem}
        result = MemoryRollback().apply(_ctx(), state)
        assert result.memory_rolled_back
        assert len(mem.retrieve()) == 1


class TestHumanConfirmation:
    def test_deny_destructive(self) -> None:
        result = HumanConfirmation(policy="deny").apply(_ctx(recent_action="delete_file"), {})
        assert result.human_approved is False
        assert result.action_blocked is True

    def test_approve_safe(self) -> None:
        result = HumanConfirmation(policy="deny").apply(_ctx(recent_action="list_files"), {})
        assert result.human_approved is True


class TestInterventionManager:
    def test_severity_gating(self) -> None:
        config = InterventionSection(
            enabled=True,
            strategies=[
                InterventionStrategy.GOAL_REVALIDATION,
                InterventionStrategy.TOOL_RESTRICTION,
                InterventionStrategy.MEMORY_ROLLBACK,
                InterventionStrategy.HUMAN_CONFIRMATION,
            ],
            min_severity="medium",
        )
        mgr = InterventionManager(config)
        assert mgr.select_strategies(DriftSeverity.LOW) == []
        assert mgr.select_strategies(DriftSeverity.MEDIUM) == ["goal_revalidation"]
        assert "human_confirmation" in mgr.select_strategies(DriftSeverity.CRITICAL)

    def test_should_intervene(self) -> None:
        config = InterventionSection(
            enabled=True,
            strategies=[InterventionStrategy.GOAL_REVALIDATION],
            min_severity="medium",
        )
        mgr = InterventionManager(config)
        low = DriftScore(
            interaction_id=1,
            behavioral_distance=0.1,
            alignment_degradation=0.0,
            violation_rate_increase=0.0,
            combined_score=0.1,
            severity=DriftSeverity.LOW,
            is_drifting=True,
        )
        assert not mgr.should_intervene(low)

        high = DriftScore(
            interaction_id=1,
            behavioral_distance=0.5,
            alignment_degradation=0.2,
            violation_rate_increase=0.1,
            combined_score=0.4,
            severity=DriftSeverity.HIGH,
            is_drifting=True,
        )
        assert mgr.should_intervene(high)
