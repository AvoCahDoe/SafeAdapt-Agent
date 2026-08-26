"""Ablation study presets A–G."""

from copy import deepcopy
from enum import Enum

from safeadapt.schemas.experiment import ExperimentConfig, MemoryMode


class AblationID(str, Enum):
    """Ablation study identifiers."""

    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"


ABLATION_NAMES = {
    AblationID.A: "No memory",
    AblationID.B: "No drift detector",
    AblationID.C: "No intervention",
    AblationID.D: "No behavioral-distance component",
    AblationID.E: "No constraint component",
    AblationID.F: "Higher drift thresholds",
    AblationID.G: "Small memory rollback",
}


def apply_ablation(base_config: ExperimentConfig, ablation_id: str) -> ExperimentConfig:
    """Apply ablation patch on a SafeAdapt-like base config (monitoring+intervention on)."""
    aid = AblationID(ablation_id)
    config = ExperimentConfig.model_validate(deepcopy(base_config.model_dump(mode="json")))
    config.experiment.name = f"{config.experiment.name}_ablation_{aid.value}"

    # Ensure full baseline then strip
    config.agent.memory = MemoryMode.PERSISTENT
    config.monitoring.enabled = True
    config.intervention.enabled = True
    if not config.intervention.strategies:
        from safeadapt.schemas.experiment import InterventionStrategy

        config.intervention.strategies = [
            InterventionStrategy.GOAL_REVALIDATION,
            InterventionStrategy.TOOL_RESTRICTION,
            InterventionStrategy.MEMORY_ROLLBACK,
            InterventionStrategy.HUMAN_CONFIRMATION,
        ]

    if aid == AblationID.A:
        config.agent.memory = MemoryMode.STATELESS
    elif aid == AblationID.B:
        config.monitoring.enabled = False
    elif aid == AblationID.C:
        config.intervention.enabled = False
    elif aid == AblationID.D:
        config.monitoring.drift_weights = {"alpha": 0.0, "beta": 0.5, "gamma": 0.5}
    elif aid == AblationID.E:
        config.monitoring.drift_weights = {"alpha": 0.5, "beta": 0.5, "gamma": 0.0}
    elif aid == AblationID.F:
        config.monitoring.drift_thresholds = {
            "low": 0.30,
            "medium": 0.50,
            "high": 0.70,
            "critical": 0.90,
        }
    elif aid == AblationID.G:
        config.intervention.rollback_n = 1

    return config


def list_ablations() -> list[str]:
    """Return ablation IDs."""
    return [a.value for a in AblationID]
