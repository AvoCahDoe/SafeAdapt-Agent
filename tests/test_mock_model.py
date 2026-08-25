"""Tests for mock LLM provider."""

import asyncio

import pytest

from safeadapt.models.mock import MockLLMProvider


class TestMockLLMProvider:
    @pytest.fixture
    def provider(self) -> MockLLMProvider:
        return MockLLMProvider(seed=42, drift_rate=0.0, violation_probability=0.0)

    def test_deterministic_output(self, provider: MockLLMProvider) -> None:
        context = {"interaction_id": 0, "task": "List all files in the project directory."}

        async def run():
            return await provider.generate("prompt", context)

        r1 = asyncio.run(run())
        r2 = asyncio.run(run())
        assert r1 == r2

    def test_returns_structured_action(self, provider: MockLLMProvider) -> None:
        context = {"interaction_id": 1, "task": "Read the report.txt file."}
        result = asyncio.run(provider.generate("prompt", context))
        assert "reason" in result
        assert "action" in result
        assert "arguments" in result

    def test_drift_mode_none_no_violations(self) -> None:
        provider = MockLLMProvider(
            seed=42, drift_rate=0.0, violation_probability=0.0, drift_mode="none"
        )
        unsafe_count = 0
        for i in range(20):
            ctx = {"interaction_id": i, "task": "List files"}
            result = asyncio.run(provider.generate("p", ctx))
            if result["action"] == "delete_file":
                unsafe_count += 1
        assert unsafe_count == 0

    def test_violation_probability_can_trigger_unsafe(self) -> None:
        provider = MockLLMProvider(
            seed=7, drift_rate=0.0, violation_probability=0.99, drift_mode="none"
        )
        unsafe_count = 0
        for i in range(10):
            ctx = {"interaction_id": i, "task": "List files"}
            result = asyncio.run(provider.generate("p", ctx))
            if result["action"] in ("delete_file",):
                unsafe_count += 1
        assert unsafe_count > 0
