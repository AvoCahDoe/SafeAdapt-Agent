"""Trajectory record schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TrajectoryRecord(BaseModel):
    """Complete record for a single agent-environment interaction."""

    interaction_id: int
    timestamp: datetime
    task: str
    goal: str
    constraints: list[str] = Field(default_factory=list)
    memory_used: list[str] = Field(default_factory=list)
    model_output: dict[str, Any] = Field(default_factory=dict)
    selected_action: str
    tool_arguments: dict[str, Any] = Field(default_factory=dict)
    environment_result: dict[str, Any] = Field(default_factory=dict)
    constraint_violations: list[str] = Field(default_factory=list)
    performance_score: float = Field(ge=0.0, le=1.0, default=0.0)
