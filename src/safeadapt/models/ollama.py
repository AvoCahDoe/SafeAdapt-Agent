"""Ollama local LLM provider."""

import os
from typing import Any

import httpx

from safeadapt.models.llm import LLMProvider
from safeadapt.models.parsing import extract_json_object, normalize_action_payload
from safeadapt.models.openai_compatible import ACTION_SYSTEM


class OllamaProvider(LLMProvider):
    """Local Ollama /api/chat provider."""

    def __init__(
        self,
        model: str = "llama3.2",
        base_url: str | None = None,
        temperature: float = 0.2,
        timeout: float = 120.0,
    ) -> None:
        self.model = model
        self.base_url = (
            base_url or os.environ.get("OLLAMA_BASE_URL") or "http://localhost:11434"
        ).rstrip("/")
        self.temperature = temperature
        self.timeout = timeout

    async def generate(self, prompt: str, context: dict[str, Any]) -> dict[str, Any]:
        """Generate a structured action via Ollama chat API."""
        tools = context.get("available_tools", [])
        user_content = f"{prompt}\n\nAvailable tools: {tools}\nRespond with JSON only."
        payload = {
            "model": self.model,
            "stream": False,
            "options": {"temperature": self.temperature},
            "messages": [
                {"role": "system", "content": ACTION_SYSTEM},
                {"role": "user", "content": user_content},
            ],
        }
        url = f"{self.base_url}/api/chat"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            body = response.json()
        content = body.get("message", {}).get("content", "")
        data = extract_json_object(content)
        return normalize_action_payload(data)

    async def complete(self, system: str, user: str) -> str:
        """Raw text completion for judge/other uses."""
        payload = {
            "model": self.model,
            "stream": False,
            "options": {"temperature": self.temperature},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        url = f"{self.base_url}/api/chat"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            body = response.json()
        return str(body.get("message", {}).get("content", ""))
