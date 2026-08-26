"""Tests for database environment."""

from safeadapt.environments.database import DatabaseEnvironment
from safeadapt.schemas.action import AgentAction


class TestDatabaseEnvironment:
    def test_query_users(self) -> None:
        env = DatabaseEnvironment()
        result = env.execute(AgentAction(reason="q", action="query", arguments={"table": "users"}))
        assert result.success
        assert len(result.output) >= 3

    def test_private_fields_redacted(self) -> None:
        env = DatabaseEnvironment()
        result = env.execute(
            AgentAction(reason="q", action="query", arguments={"table": "users", "id": 2})
        )
        assert result.success
        assert result.output[0]["email"] == "[REDACTED]"

    def test_delete_protected_blocked(self) -> None:
        env = DatabaseEnvironment()
        result = env.execute(
            AgentAction(
                reason="d",
                action="delete",
                arguments={"table": "users", "id": 3, "confirmed": True},
            )
        )
        assert not result.success
        assert any("protected" in v for v in result.constraint_violations)

    def test_delete_requires_confirmation(self) -> None:
        env = DatabaseEnvironment()
        result = env.execute(
            AgentAction(reason="d", action="delete", arguments={"table": "orders", "id": 101})
        )
        assert not result.success
        assert result.requires_confirmation

    def test_insert_and_delete(self) -> None:
        env = DatabaseEnvironment()
        ins = env.execute(
            AgentAction(
                reason="i",
                action="insert",
                arguments={"table": "orders", "row": {"user_id": 1, "amount": 5.0}},
            )
        )
        assert ins.success
        row_id = ins.output["inserted"]
        deleted = env.execute(
            AgentAction(
                reason="d",
                action="delete",
                arguments={"table": "orders", "id": row_id, "confirmed": True},
            )
        )
        assert deleted.success
