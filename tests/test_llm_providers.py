"""Tests for LLM parsing and providers (mocked HTTP)."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from safeadapt.models.judge import LLMJudge
from safeadapt.models.ollama import OllamaProvider
from safeadapt.models.openai_compatible import OpenAICompatibleProvider
from safeadapt.models.parsing import extract_json_object, normalize_action_payload
from safeadapt.schemas.goal import GoalSpecification
from safeadapt.schemas.trajectory import TrajectoryRecord
from datetime import datetime, timezone


class TestParsing:
    def test_extract_json_raw(self) -> None:
        data = extract_json_object('{"action": "list_files", "reason": "x", "arguments": {}}')
        assert data["action"] == "list_files"

    def test_extract_json_fenced(self) -> None:
        data = extract_json_object('```json\n{"action": "read_file", "arguments": {"path": "/a"}}\n```')
        assert normalize_action_payload(data)["action"] == "read_file"


class TestOpenAICompatible:
    @pytest.mark.asyncio
    async def test_generate_parses_response(self) -> None:
        provider = OpenAICompatibleProvider(
            model="deepseek-chat",
            api_key="test-key",
            base_url="https://api.deepseek.com/v1",
        )
        fake_body = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "reason": "list",
                                "action": "list_files",
                                "arguments": {"directory": "/project"},
                            }
                        )
                    }
                }
            ]
        }
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = fake_body

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("safeadapt.models.openai_compatible.httpx.AsyncClient", return_value=mock_client):
            result = await provider.generate(
                "GOAL: organize",
                {"available_tools": ["list_files"], "interaction_id": 0},
            )
        assert result["action"] == "list_files"


class TestOllama:
    @pytest.mark.asyncio
    async def test_generate_parses_response(self) -> None:
        provider = OllamaProvider(model="llama3.2")
        fake_body = {
            "message": {
                "content": '{"reason": "q", "action": "query", "arguments": {"table": "users"}}'
            }
        }
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = fake_body
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("safeadapt.models.ollama.httpx.AsyncClient", return_value=mock_client):
            result = await provider.generate("prompt", {"available_tools": ["query"]})
        assert result["action"] == "query"


class TestJudge:
    @pytest.mark.asyncio
    async def test_score(self) -> None:
        class FakeCompleter:
            async def complete(self, system: str, user: str) -> str:
                return json.dumps(
                    {
                        "goal_adherence": 0.8,
                        "preference_adherence": 0.7,
                        "quality": 0.75,
                        "explanation": "ok",
                    }
                )

        judge = LLMJudge(FakeCompleter(), model_name="fake:model")
        traj = TrajectoryRecord(
            interaction_id=0,
            timestamp=datetime.now(timezone.utc),
            task="list files",
            goal="organize",
            selected_action="list_files",
            performance_score=1.0,
            environment_result={"success": True},
        )
        goal = GoalSpecification(primary_goal="organize")
        out = await judge.score(traj, goal)
        assert out["judge_score"] == 0.8
        assert out["judge_model"] == "fake:model"
