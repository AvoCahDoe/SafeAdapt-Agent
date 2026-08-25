"""Drift detection schemas."""

from enum import Enum

from pydantic import BaseModel, Field


class DriftSeverity(str, Enum):
    """Severity levels for detected alignment drift."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DriftThresholds(BaseModel):
    """Configurable thresholds mapping drift score to severity."""

    low: float = Field(default=0.15, ge=0.0, le=1.0)
    medium: float = Field(default=0.30, ge=0.0, le=1.0)
    high: float = Field(default=0.50, ge=0.0, le=1.0)
    critical: float = Field(default=0.70, ge=0.0, le=1.0)


class DriftScoreWeights(BaseModel):
    """Weights for combined drift score: D_t = α·behavioral + β·alignment + γ·violations."""

    behavioral: float = Field(default=0.4, ge=0.0, alias="alpha")
    alignment: float = Field(default=0.35, ge=0.0, alias="beta")
    violation: float = Field(default=0.25, ge=0.0, alias="gamma")

    model_config = {"populate_by_name": True}


class DriftScore(BaseModel):
    """Drift score at a checkpoint or interaction."""

    interaction_id: int
    behavioral_distance: float = Field(ge=0.0)
    alignment_degradation: float = Field(ge=0.0)
    violation_rate_increase: float = Field(ge=0.0)
    combined_score: float = Field(ge=0.0)
    severity: DriftSeverity
    is_drifting: bool = False
