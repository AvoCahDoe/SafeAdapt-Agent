"""Tests for agent action validation."""

from safeadapt.agents.validation import validate_action
from safeadapt.schemas.action import AgentAction
from safeadapt.schemas.goal import GoalSpecification

GOAL = GoalSpecification(
    primary_goal="Organize files",
    forbidden_actions=["delete_protected_file"],
    approval_required_actions=["delete_file"],
)

TOOLS = ["list_files", "read_file", "write_file", "rename_file", "delete_file"]


class TestActionValidation:
    def test_valid_action(self) -> None:
        action = AgentAction(reason="list", action="list_files", arguments={})
        result = validate_action(action, GOAL, TOOLS)
        assert result.valid

    def test_unknown_tool_rejected(self) -> None:
        action = AgentAction(reason="bad", action="shell_exec", arguments={})
        result = validate_action(action, GOAL, TOOLS)
        assert result.rejected
        assert "Unknown tool" in result.violations[0]

    def test_forbidden_action_rejected(self) -> None:
        action = AgentAction(reason="bad", action="delete_protected_file", arguments={})
        result = validate_action(action, GOAL, TOOLS)
        assert result.rejected
        assert "Forbidden" in result.violations[0]

    def test_approval_required_without_confirm(self) -> None:
        action = AgentAction(reason="delete", action="delete_file", arguments={})
        result = validate_action(action, GOAL, TOOLS)
        assert result.rejected
        assert result.requires_confirmation

    def test_approval_with_confirm_passes_validation(self) -> None:
        action = AgentAction(
            reason="delete",
            action="delete_file",
            arguments={"path": "/project/notes.txt", "confirmed": True},
        )
        result = validate_action(action, GOAL, TOOLS)
        assert result.valid
