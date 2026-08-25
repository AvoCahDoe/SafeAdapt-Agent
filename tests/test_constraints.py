"""Tests for safety constraint checking."""

from safeadapt.environments.constraints import (
    check_action_against_goal,
    check_delete_file,
    check_read_file,
)
from safeadapt.schemas.action import AgentAction
from safeadapt.schemas.environment import VirtualFile
from safeadapt.schemas.goal import GoalSpecification


GOAL = GoalSpecification(
    primary_goal="Organize files",
    safety_constraints=["Never expose private information"],
    forbidden_actions=["delete_protected_file"],
    approval_required_actions=["delete_file"],
)


class TestConstraints:
    def test_delete_protected_violation(self) -> None:
        file = VirtualFile(path="/project/x.txt", protected=True)
        violations, _ = check_delete_file(file, {"confirmed": True})
        assert any("protected" in v for v in violations)

    def test_delete_requires_confirmation(self) -> None:
        file = VirtualFile(path="/project/x.txt")
        violations, requires = check_delete_file(file, {})
        assert not violations
        assert requires

    def test_read_private_violation(self) -> None:
        file = VirtualFile(path="/project/secret.txt", private=True)
        violations = check_read_file(file, expose_private=True)
        assert len(violations) == 1

    def test_forbidden_action_in_goal(self) -> None:
        action = AgentAction(reason="x", action="delete_protected_file", arguments={})
        violations, _ = check_action_against_goal(action, GOAL)
        assert "Forbidden action" in violations[0]

    def test_approval_required_without_confirm(self) -> None:
        action = AgentAction(reason="x", action="delete_file", arguments={})
        violations, requires = check_action_against_goal(action, GOAL)
        assert not violations
        assert requires
