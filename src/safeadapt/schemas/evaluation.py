"""Evaluation and intervention record schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AlignmentWeights(BaseModel):
    """Configurable weights for overall alignment scoring."""

    goal_weight: float = Field(default=0.30, ge=0.0, le=1.0)
    safety_weight: float = Field(default=0.40, ge=0.0, le=1.0)
    preference_weight: float = Field(default=0.15, ge=0.0, le=1.0)
    constraint_weight: float = Field(default=0.15, ge=0.0, le=1.0)


class EvaluationRecord(BaseModel):
    """Per-interaction or per-checkpoint evaluation result."""

    interaction_id: int
    timestamp: datetime
    goal_adherence: float = Field(ge=0.0, le=1.0)
    safety_adherence: float = Field(ge=0.0, le=1.0)
    preference_adherence: float = Field(ge=0.0, le=1.0)
    constraint_adherence: float = Field(ge=0.0, le=1.0)
    overall_alignment: float = Field(ge=0.0, le=1.0)
    task_success: bool = False
    objective_violations: list[str] = Field(default_factory=list)
    judge_score: float | None = None
    judge_model: str | None = None
    judge_prompt_version: str | None = None
    judge_raw_response: str | None = None


class InterventionRecord(BaseModel):
    """Record of a drift-triggered intervention."""

    interaction_id: int
    timestamp: datetime
    strategy: str
    severity: str
    drift_score: float
    details: dict[str, Any] = Field(default_factory=dict)


class FailureRecord(BaseModel):
    """Classified safety failure for post-hoc analysis."""

    interaction_id: int
    category: str
    severity: str
    description: str
    preceding_events: list[str] = Field(default_factory=list)
    intervention: str | None = None
