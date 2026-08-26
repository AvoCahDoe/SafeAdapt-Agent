"""Shared helpers for LLM JSON action parsing."""

import json
import re
from typing import Any


def extract_json_object(text: str) -> dict[str, Any]:
    """Extract a JSON object from model text (raw or fenced)."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        data = json.loads(match.group(0))
        if isinstance(data, dict):
            return data
    raise ValueError(f"Could not parse JSON from model response: {text[:200]}")


def normalize_action_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize to AgentAction-compatible dict."""
    action = data.get("action") or data.get("tool") or data.get("name")
    if not action:
        raise ValueError(f"Missing action field in model output: {data}")
    return {
        "reason": str(data.get("reason", data.get("explanation", ""))),
        "action": str(action),
        "arguments": dict(data.get("arguments") or data.get("args") or {}),
    }
