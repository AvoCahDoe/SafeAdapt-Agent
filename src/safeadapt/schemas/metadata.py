"""Experiment run metadata schemas."""

from datetime import datetime

from pydantic import BaseModel


class RunMetadata(BaseModel):
    """Reproducibility metadata for an experiment run."""

    experiment_id: str
    seed: int
    model: str
    environment: str
    scenario: str
    interactions: int
    timestamp: datetime
    git_commit: str | None = None
    config_hash: str
