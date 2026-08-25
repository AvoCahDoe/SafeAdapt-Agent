"""Structured agent action schemas."""

from typing import Any

from pydantic import BaseModel, Field


class AgentAction(BaseModel):
    """JSON-structured action output from the agent model."""

    reason: str
    action: str
    arguments: dict[str, Any] = Field(default_factory=dict)
