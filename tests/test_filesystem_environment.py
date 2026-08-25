"""Tests for filesystem environment."""

import pytest

from safeadapt.environments.filesystem import FileManagerEnvironment
from safeadapt.schemas.action import AgentAction


@pytest.fixture
def env() -> FileManagerEnvironment:
    return FileManagerEnvironment()


class TestFileManagerEnvironment:
    def test_list_files(self, env: FileManagerEnvironment) -> None:
        result = env.execute(AgentAction(
            reason="list", action="list_files", arguments={"directory": "/project"}
        ))
        assert result.success
        assert len(result.output) >= 4

    def test_read_public_file(self, env: FileManagerEnvironment) -> None:
        result = env.execute(AgentAction(
            reason="read", action="read_file", arguments={"path": "/project/report.txt"}
        ))
        assert result.success
        assert "Quarterly report" in result.output["content"]

    def test_read_private_file_redacted(self, env: FileManagerEnvironment) -> None:
        result = env.execute(AgentAction(
            reason="read",
            action="read_file",
            arguments={"path": "/project/private_credentials.txt"},
        ))
        assert result.success
        assert result.output["content"] == "[REDACTED: private file]"

    def test_delete_protected_file_blocked(self, env: FileManagerEnvironment) -> None:
        result = env.execute(AgentAction(
            reason="delete",
            action="delete_file",
            arguments={"path": "/project/final_report.pdf", "confirmed": True},
        ))
        assert not result.success
        assert any("protected" in v for v in result.constraint_violations)

    def test_delete_requires_confirmation(self, env: FileManagerEnvironment) -> None:
        result = env.execute(AgentAction(
            reason="delete",
            action="delete_file",
            arguments={"path": "/project/notes.txt"},
        ))
        assert not result.success
        assert result.requires_confirmation

    def test_delete_with_confirmation(self, env: FileManagerEnvironment) -> None:
        result = env.execute(AgentAction(
            reason="delete",
            action="delete_file",
            arguments={"path": "/project/notes.txt", "confirmed": True},
        ))
        assert result.success
        assert result.output["deleted"] is True

    def test_write_and_rename(self, env: FileManagerEnvironment) -> None:
        write = env.execute(AgentAction(
            reason="write",
            action="write_file",
            arguments={"path": "/project/new.txt", "content": "hello"},
        ))
        assert write.success

        rename = env.execute(AgentAction(
            reason="rename",
            action="rename_file",
            arguments={
                "old_path": "/project/new.txt",
                "new_path": "/project/renamed.txt",
            },
        ))
        assert rename.success

    def test_observe_hides_content(self, env: FileManagerEnvironment) -> None:
        obs = env.observe()
        for f in obs["files"]:
            assert "content" not in f

    def test_reset_restores_files(self, env: FileManagerEnvironment) -> None:
        env.execute(AgentAction(
            reason="delete",
            action="delete_file",
            arguments={"path": "/project/notes.txt", "confirmed": True},
        ))
        env.reset()
        result = env.execute(AgentAction(
            reason="read",
            action="read_file",
            arguments={"path": "/project/notes.txt"},
        ))
        assert result.success

    def test_unknown_tool(self, env: FileManagerEnvironment) -> None:
        result = env.execute(AgentAction(
            reason="bad", action="shell_exec", arguments={}
        ))
        assert not result.success
