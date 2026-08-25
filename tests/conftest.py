"""Shared pytest fixtures."""

from pathlib import Path

import pytest

from safeadapt.schemas.experiment import ExperimentConfig, ExperimentSection


@pytest.fixture
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def test_foundation_config_path(project_root: Path) -> Path:
    """Path to the test foundation experiment config."""
    return project_root / "configs" / "experiments" / "test_foundation.yaml"


@pytest.fixture
def minimal_experiment_config() -> ExperimentConfig:
    """Minimal valid experiment configuration."""
    return ExperimentConfig(
        experiment=ExperimentSection(
            name="unit_test",
            seed=123,
            interactions=10,
        )
    )
