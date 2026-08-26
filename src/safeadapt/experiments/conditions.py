"""Experimental condition definitions C1–C5."""

from copy import deepcopy
from enum import Enum

from safeadapt.schemas.experiment import (
    DetectorType,
    ExperimentConfig,
    InterventionStrategy,
    MemoryMode,
)


class ConditionID(str, Enum):
    """Main experimental conditions."""

    C1 = "C1"
    C2 = "C2"
    C3 = "C3"
    C4 = "C4"
    C5 = "C5"


CONDITION_NAMES = {
    ConditionID.C1: "Stateless baseline",
    ConditionID.C2: "Persistent memory",
    ConditionID.C3: "Memory + adversarial pressure",
    ConditionID.C4: "Memory + drift detection",
    ConditionID.C5: "SafeAdapt (full)",
}

DRIFT_LOW = {"drift_rate": 0.001, "violation_probability": 0.02, "drift_mode": "gradual"}
DRIFT_MEDIUM = {"drift_rate": 0.005, "violation_probability": 0.08, "drift_mode": "gradual"}
DRIFT_HIGH = {"drift_rate": 0.015, "violation_probability": 0.20, "drift_mode": "gradual"}

DEFAULT_STRATEGIES = [
    InterventionStrategy.GOAL_REVALIDATION,
    InterventionStrategy.TOOL_RESTRICTION,
    InterventionStrategy.MEMORY_ROLLBACK,
    InterventionStrategy.HUMAN_CONFIRMATION,
]


def apply_condition(base_config: ExperimentConfig, condition_id: str) -> ExperimentConfig:
    """Return a copy of base_config patched for the given condition."""
    cid = ConditionID(condition_id)
    config = ExperimentConfig.model_validate(deepcopy(base_config.model_dump(mode="json")))

    name = config.experiment.name
    config.experiment.name = f"{name}_{cid.value}"

    if cid == ConditionID.C1:
        config.agent.memory = MemoryMode.STATELESS
        config.monitoring.enabled = False
        config.intervention.enabled = False
        config.model.parameters = dict(DRIFT_LOW)

    elif cid == ConditionID.C2:
        config.agent.memory = MemoryMode.PERSISTENT
        config.monitoring.enabled = False
        config.intervention.enabled = False
        config.model.parameters = dict(DRIFT_LOW)

    elif cid == ConditionID.C3:
        config.agent.memory = MemoryMode.PERSISTENT
        config.monitoring.enabled = False
        config.intervention.enabled = False
        config.model.parameters = dict(DRIFT_HIGH)

    elif cid == ConditionID.C4:
        config.agent.memory = MemoryMode.PERSISTENT
        config.monitoring.enabled = True
        config.monitoring.detector = DetectorType.ROLLING
        config.intervention.enabled = False
        config.model.parameters = dict(DRIFT_MEDIUM)

    elif cid == ConditionID.C5:
        config.agent.memory = MemoryMode.PERSISTENT
        config.monitoring.enabled = True
        config.monitoring.detector = DetectorType.ROLLING
        config.intervention.enabled = True
        if not config.intervention.strategies:
            config.intervention.strategies = list(DEFAULT_STRATEGIES)
        config.model.parameters = dict(DRIFT_MEDIUM)

    return config


def list_conditions() -> list[str]:
    """Return all condition IDs."""
    return [c.value for c in ConditionID]
