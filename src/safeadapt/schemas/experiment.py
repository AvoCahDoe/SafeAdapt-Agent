"""Experiment configuration schemas."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from safeadapt.schemas.evaluation import AlignmentWeights


class MemoryMode(str, Enum):
    """Agent memory mode for experiments."""

    STATELESS = "stateless"
    PERSISTENT = "persistent"


class DetectorType(str, Enum):
    """Drift detector implementation."""

    ROLLING = "rolling"
    CUSUM = "cusum"
    JSD = "jsd"


class InterventionStrategy(str, Enum):
    """Available intervention strategies."""

    GOAL_REVALIDATION = "goal_revalidation"
    TOOL_RESTRICTION = "tool_restriction"
    MEMORY_ROLLBACK = "memory_rollback"
    HUMAN_CONFIRMATION = "human_confirmation"


class ExperimentSection(BaseModel):
    """Top-level experiment parameters."""

    name: str
    seed: int = 42
    interactions: int = 100


class ModelSection(BaseModel):
    """LLM provider configuration."""

    provider: str = "mock"
    name: str = "mock-agent"
    parameters: dict[str, Any] = Field(default_factory=dict)


class AgentSection(BaseModel):
    """Agent configuration."""

    memory: MemoryMode = MemoryMode.STATELESS


class EnvironmentSection(BaseModel):
    """Simulated environment configuration."""

    type: str = "filesystem"
    config: dict[str, Any] = Field(default_factory=dict)


class ScenarioSection(BaseModel):
    """Benchmark scenario configuration."""

    type: str = "normal_workload"
    config: dict[str, Any] = Field(default_factory=dict)


class MonitoringSection(BaseModel):
    """Drift monitoring configuration."""

    enabled: bool = False
    window_size: int = 50
    detector: DetectorType = DetectorType.ROLLING
    drift_thresholds: dict[str, float] = Field(default_factory=dict)
    drift_weights: dict[str, float] = Field(default_factory=dict)


class InterventionSection(BaseModel):
    """Intervention configuration."""

    enabled: bool = False
    strategies: list[InterventionStrategy] = Field(default_factory=list)
    human_policy: str = "deny"  # deny | approve | approve_safe_only
    restriction_duration: int = 10
    rollback_n: int = 5
    min_severity: str = "medium"


class JudgeSection(BaseModel):
    """Optional LLM judge configuration."""

    enabled: bool = False
    model: str | None = None
    prompt_version: str = "v1"


class EvaluationSection(BaseModel):
    """Evaluation configuration."""

    alignment: AlignmentWeights = Field(default_factory=AlignmentWeights)
    judge: JudgeSection = Field(default_factory=JudgeSection)


class ExperimentConfig(BaseModel):
    """Complete experiment configuration loaded from YAML."""

    experiment: ExperimentSection
    model: ModelSection = Field(default_factory=ModelSection)
    agent: AgentSection = Field(default_factory=AgentSection)
    environment: EnvironmentSection = Field(default_factory=EnvironmentSection)
    scenario: ScenarioSection = Field(default_factory=ScenarioSection)
    monitoring: MonitoringSection = Field(default_factory=MonitoringSection)
    intervention: InterventionSection = Field(default_factory=InterventionSection)
    evaluation: EvaluationSection = Field(default_factory=EvaluationSection)
