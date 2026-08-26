"""Tests for experimental conditions."""

from safeadapt.experiments.conditions import apply_condition, list_conditions
from safeadapt.schemas.experiment import ExperimentConfig, ExperimentSection, MemoryMode


def _base() -> ExperimentConfig:
    return ExperimentConfig(experiment=ExperimentSection(name="test", seed=1, interactions=10))


class TestConditions:
    def test_list_conditions(self) -> None:
        assert list_conditions() == ["C1", "C2", "C3", "C4", "C5"]

    def test_c1_stateless(self) -> None:
        cfg = apply_condition(_base(), "C1")
        assert cfg.agent.memory == MemoryMode.STATELESS
        assert not cfg.monitoring.enabled
        assert not cfg.intervention.enabled

    def test_c3_adversarial(self) -> None:
        cfg = apply_condition(_base(), "C3")
        assert cfg.model.parameters["violation_probability"] >= 0.15
        assert not cfg.monitoring.enabled

    def test_c4_monitoring_only(self) -> None:
        cfg = apply_condition(_base(), "C4")
        assert cfg.monitoring.enabled
        assert not cfg.intervention.enabled

    def test_c5_full(self) -> None:
        cfg = apply_condition(_base(), "C5")
        assert cfg.monitoring.enabled
        assert cfg.intervention.enabled
        assert len(cfg.intervention.strategies) >= 1
